"""Async LRS data backend for Ralph."""

import logging
from io import IOBase
from typing import AsyncIterator, Iterable, Optional, Union
from urllib.parse import ParseResult, parse_qs, urljoin, urlparse

from httpx import AsyncClient, HTTPError, HTTPStatusError, RequestError
from pydantic import AnyHttpUrl, PositiveInt, parse_obj_as

from ralph.backends.data.base import (
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseOperationType,
    DataBackendStatus,
)
from ralph.backends.data.lrs import LRSDataBackendSettings, StatementResponse
from ralph.backends.lrs.base import LRSStatementsQuery
from ralph.exceptions import BackendException
from ralph.utils import async_parse_dict_to_bytes, iter_by_batch, parse_iterable_to_dict

logger = logging.getLogger(__name__)


class AsyncLRSDataBackend(
    BaseAsyncDataBackend[LRSDataBackendSettings, LRSStatementsQuery],
    AsyncWritable,
):
    """Asynchronous LRS data backend."""

    name = "async_lrs"
    default_operation_type = BaseOperationType.CREATE
    unsupported_operation_types = {
        BaseOperationType.APPEND,
        BaseOperationType.UPDATE,
        BaseOperationType.DELETE,
    }

    def __init__(self, settings: Optional[LRSDataBackendSettings] = None) -> None:
        """Instantiate the LRS HTTP (basic auth) backend client.

        Args:
            settings (LRSDataBackendSettings or None): The LRS data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self.base_url = parse_obj_as(AnyHttpUrl, self.settings.BASE_URL)
        self.auth = (self.settings.USERNAME, self.settings.PASSWORD)
        self._client = None

    @property
    def client(self) -> AsyncClient:
        """Create a `httpx.AsyncClient` if it doesn't exist."""
        if not self._client:
            headers = self.settings.HEADERS.dict(by_alias=True)
            self._client = AsyncClient(auth=self.auth, headers=headers)
        return self._client

    async def status(self) -> DataBackendStatus:
        """HTTP backend check for server status."""
        status_url = urljoin(self.base_url, self.settings.STATUS_ENDPOINT)
        try:
            response = await self.client.get(status_url)
            response.raise_for_status()
        except RequestError:
            logger.error("Unable to request the server")
            return DataBackendStatus.AWAY
        except HTTPStatusError:
            logger.error("Response raised an HTTP status of 4xx or 5xx")
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    async def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, LRSStatementsQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        prefetch: Optional[PositiveInt] = None,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[AsyncIterator[bytes], AsyncIterator[dict]]:
        """Get statements from LRS `target` endpoint.

        The `read` method defined in the LRS specification returns `statements` array
        and `more` IRL. The latter is required when the returned `statement` list has
        been limited.

        Args:
            query (str, LRSStatementsQuery):  The query to select records to read.
            target (str): Endpoint from which to read data (e.g. `/statements`).
                If target is `None`, `/xAPI/statements` default endpoint is used.
            chunk_size (int or None): The number of records or bytes to read in one
                batch, depending on whether the records are dictionaries or bytes.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
                If the records are dictionaries and `raw_output` is set to `True`, they
                are encoded as JSON.
                If the records are bytes and `raw_output` is set to `False`, they are
                decoded as JSON by line.
            ignore_errors (bool): If `True`, errors during the read operation
                are ignored and logged. If `False` (default), a `BackendException`
                is raised if an error occurs.
            prefetch (int): The number of records to prefetch (queue) while yielding.
                If `prefetch` is `None` it defaults to `1` - no records are prefetched.
            max_statements: The maximum number of statements to yield.
        """
        statements = super().read(
            query,
            target,
            chunk_size,
            raw_output,
            ignore_errors,
            prefetch,
            max_statements,
        )
        async for statement in statements:
            yield statement

    async def _read_bytes(
        self,
        query: LRSStatementsQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
    ) -> AsyncIterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        statements = self._read_dicts(query, target, chunk_size, ignore_errors)
        async for statement in async_parse_dict_to_bytes(
            statements, self.settings.LOCALE_ENCODING, ignore_errors
        ):
            yield statement

    async def _read_dicts(
        self,
        query: LRSStatementsQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> AsyncIterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        if not target:
            target = self.settings.STATEMENTS_ENDPOINT

        if query.limit:
            logger.warning(
                "The limit query parameter value is overwritten by the chunk_size "
                "parameter value."
            )

        query.limit = chunk_size

        # Create request URL
        target = ParseResult(
            scheme=urlparse(self.base_url).scheme,
            netloc=urlparse(self.base_url).netloc,
            path=target,
            query="",
            params="",
            fragment="",
        ).geturl()

        statements = self._fetch_statements(
            target=target,
            query_params=query.dict(exclude_none=True, exclude_unset=True),
        )

        # Iterate through results
        try:
            async for statement in statements:
                yield statement
        except HTTPError as error:
            msg = "Failed to fetch statements: %s"
            logger.error(msg, error)
            raise BackendException(msg % (error,)) from error

    async def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
        concurrency: Optional[int] = None,
    ) -> int:
        """Write `data` records to the `target` endpoint and return their count.

        Args:
            data: (Iterable): The data to write.
            target (str or None): Endpoint in which to write data (e.g. `/statements`).
                If `target` is `None`, `/xAPI/statements` default endpoint is used.
            chunk_size (int or None): The number of records or bytes to write in one
                batch, depending on whether `data` contains dictionaries or bytes.
                If `chunk_size` is `None`, a default value is used instead.
            ignore_errors (bool): If `True`, errors during the write operation
                are ignored and logged. If `False` (default), a `BackendException`
                is raised if an error occurs.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.
            concurrency (int): The number of chunks to write concurrently.
                If `None` it defaults to `1`.
        """
        return await super().write(
            data, target, chunk_size, ignore_errors, operation_type, concurrency
        )

    async def _write_bytes(  # noqa: PLR0913
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        statements = parse_iterable_to_dict(data, ignore_errors)
        return await self._write_dicts(
            statements, target, chunk_size, ignore_errors, operation_type
        )

    async def _write_dicts(  # noqa: PLR0913
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,  # noqa: ARG002
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        if not target:
            target = self.settings.STATEMENTS_ENDPOINT

        target = ParseResult(
            scheme=urlparse(self.base_url).scheme,
            netloc=urlparse(self.base_url).netloc,
            path=target,
            query="",
            params="",
            fragment="",
        ).geturl()

        logger.debug(
            "Start writing to the %s endpoint (chunk size: %s)", target, chunk_size
        )

        count = 0
        for chunk in iter_by_batch(data, chunk_size):
            count += await self._post_and_raise_for_status(target, chunk, ignore_errors)

        logger.debug("Posted %d statements", count)
        return count

    async def close(self) -> None:
        """Close the `httpx.AsyncClient`.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            logger.warning("No backend client to close.")
            return

        await self.client.aclose()

    async def _fetch_statements(self, target, query_params: dict):
        """Fetch statements from a LRS."""
        while True:
            response = await self.client.get(target, params=query_params)
            response.raise_for_status()
            statements_response = StatementResponse(**response.json())
            statements = statements_response.statements
            if isinstance(statements, dict):
                statements = [statements]

            for statement in statements:
                yield statement

            if not statements_response.more:
                break

            query_params.update(parse_qs(urlparse(statements_response.more).query))

    async def _post_and_raise_for_status(self, target, chunk, ignore_errors):
        """POST chunk of statements to `target` and return the number of insertions."""
        try:
            request = await self.client.post(target, json=chunk)
            request.raise_for_status()
            return len(chunk)
        except HTTPError as error:
            msg = "Failed to post statements: %s"
            if ignore_errors:
                logger.warning(msg, error)
                return 0
            logger.error(msg, error)
            raise BackendException(msg % (error,)) from error
