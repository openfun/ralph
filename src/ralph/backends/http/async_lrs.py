"""Async LRS HTTP backend for Ralph."""

import asyncio
import json
import logging
from itertools import chain
from typing import Iterable, Iterator, List, Optional, Union
from urllib.parse import ParseResult, parse_qs, urljoin, urlparse

from httpx import AsyncClient, HTTPError, HTTPStatusError, RequestError
from pydantic import AnyHttpUrl, BaseModel, Field, parse_obj_as
from pydantic.types import PositiveInt

from ralph.backends.lrs.base import LRSStatementsQuery
from ralph.conf import BaseSettingsConfig, HeadersParameters
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import gather_with_limited_concurrency, iter_by_batch

from .base import (
    BaseHTTPBackend,
    BaseHTTPBackendSettings,
    HTTPBackendStatus,
    OperationType,
    enforce_query_checks,
)

logger = logging.getLogger(__name__)


class LRSHeaders(HeadersParameters):
    """Pydantic model for LRS headers."""

    X_EXPERIENCE_API_VERSION: str = Field("1.0.3", alias="X-Experience-API-Version")
    CONTENT_TYPE: str = Field("application/json", alias="content-type")


class LRSHTTPBackendSettings(BaseHTTPBackendSettings):
    """LRS HTTP backend default configuration.

    Attributes:
        BASE_URL (AnyHttpUrl): LRS server URL.
        USERNAME (str): Basic auth username for LRS authentication.
        PASSWORD (str): Basic auth password for LRS authentication.
        HEADERS (dict): Headers defined for the LRS server connection.
        STATUS_ENDPOINT (str): Endpoint used to check server status.
        STATEMENTS_ENDPOINT (str): Default endpoint for LRS statements resource.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__HTTP__LRS__"

    BASE_URL: AnyHttpUrl = Field("http://0.0.0.0:8100")
    USERNAME: str = "ralph"
    PASSWORD: str = "secret"
    HEADERS: LRSHeaders = LRSHeaders()
    STATUS_ENDPOINT: str = "/__heartbeat__"
    STATEMENTS_ENDPOINT: str = "/xAPI/statements"


class StatementResponse(BaseModel):
    """Pydantic model for `get` statements response."""

    statements: Union[List[dict], dict]
    more: Optional[str]


class AsyncLRSHTTPBackend(BaseHTTPBackend):
    """Asynchronous LRS HTTP backend."""

    name = "async_lrs"
    query = LRSStatementsQuery
    default_operation_type = OperationType.CREATE
    settings_class = LRSHTTPBackendSettings

    def __init__(self, settings: Optional[LRSHTTPBackendSettings] = None):
        """Instantiate the LRS HTTP (basic auth) backend client.

        Args:
            settings (LRSHTTPBackendSettings or None): The LRS HTTP backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings = settings if settings else self.settings_class()

        self.base_url = parse_obj_as(AnyHttpUrl, self.settings.BASE_URL)
        self.auth = (self.settings.USERNAME, self.settings.PASSWORD)

    async def status(self) -> HTTPBackendStatus:
        """HTTP backend check for server status."""
        status_url = urljoin(self.base_url, self.settings.STATUS_ENDPOINT)

        try:
            async with AsyncClient() as client:
                response = await client.get(status_url)
            response.raise_for_status()
        except RequestError:
            msg = "Unable to request the server"
            logger.error(msg)
            return HTTPBackendStatus.AWAY
        except HTTPStatusError:
            msg = "Response raised an HTTP status of 4xx or 5xx"
            logger.error(msg)
            return HTTPBackendStatus.ERROR

        return HTTPBackendStatus.OK

    async def list(
        self,
        target: Optional[str] = None,
        details: bool = False,  # noqa: ARG002
        new: bool = False,  # noqa: ARG002
    ) -> Iterator[Union[str, dict]]:
        """Raise error for unsupported `list` method."""
        msg = "LRS HTTP backend does not support `list` method, cannot list from %s"

        logger.error(msg, target)
        raise NotImplementedError(msg % target)

    @enforce_query_checks
    async def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, LRSStatementsQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[PositiveInt] = 500,
        raw_output: bool = False,
        ignore_errors: bool = False,  # noqa: ARG002
        greedy: bool = True,
        max_statements: Optional[PositiveInt] = None,
    ) -> Iterator[Union[bytes, dict]]:
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
            greedy: If set to True, the client will fetch all available pages even
                before the statements yielded by the generator are consumed. Caution:
                this might potentially lead to large amounts of API calls and to the
                memory filling up.
            max_statements: The maximum number of statements to yield.
        """
        if not target:
            target = self.settings.STATEMENTS_ENDPOINT

        if query and query.limit:
            logger.warning(
                "The limit query parameter value is overwritten by the chunk_size "
                "parameter value."
            )

        if query is None:
            query = LRSStatementsQuery()

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

        # Select the appropriate fetch function
        if greedy:
            statements_async_generator = self._greedy_fetch_statements(
                target, raw_output, query.dict(exclude_none=True, exclude_unset=True)
            )
        else:
            statements_async_generator = self._fetch_statements(
                target=target,
                raw_output=raw_output,
                query_params=query.dict(exclude_none=True, exclude_unset=True),
            )

        # Iterate through results
        counter = 0
        try:
            async for statement in statements_async_generator:
                if max_statements and (counter >= max_statements):
                    break
                yield statement
                counter += 1
        except HTTPError as error:
            msg = "Failed to fetch statements."
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error

    async def write(  # noqa: PLR0913
        self,
        data: Union[Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[PositiveInt] = 500,
        ignore_errors: bool = False,
        operation_type: Optional[OperationType] = None,
        simultaneous: bool = False,
        max_num_simultaneous: Optional[PositiveInt] = None,
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
            operation_type (OperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `OperationType`.
            simultaneous (bool): If `True`, chunks requests will be made concurrently.
                If `False` (default), chunks will be sent sequentially
            max_num_simultaneous (int or None): If simultaneous is `True`, the maximum
                number of chunks to POST concurrently. If `None` (default), no limit is
                set.
        """
        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return 0

        if not operation_type:
            operation_type = self.default_operation_type

        if operation_type in (
            OperationType.APPEND,
            OperationType.UPDATE,
            OperationType.DELETE,
        ):
            msg = f"{operation_type.value} operation type is not supported."
            logger.error(msg)
            raise BackendParameterException(msg)

        if not target:
            target = self.settings.STATEMENTS_ENDPOINT

        if not chunk_size:
            chunk_size = 500

        target = ParseResult(
            scheme=urlparse(self.base_url).scheme,
            netloc=urlparse(self.base_url).netloc,
            path=target,
            query="",
            params="",
            fragment="",
        ).geturl()

        if (max_num_simultaneous is not None) and max_num_simultaneous < 1:
            msg = "max_num_simultaneous must be a strictly positive integer"
            logger.error(msg)
            raise BackendParameterException(msg)

        if (not simultaneous) and (max_num_simultaneous is not None):
            msg = "max_num_simultaneous can only be used with `simultaneous=True`"
            logger.error(msg)
            raise BackendParameterException(msg)

        # Gather only one chunk at a time when not using the simultaneous option
        if not simultaneous:
            max_num_simultaneous = 1

        data = chain((first_record,), data)

        logger.debug(
            "Start writing to the %s endpoint (chunk size: %s)", target, chunk_size
        )

        # Create tasks
        tasks = set()
        for chunk in iter_by_batch(data, chunk_size):
            tasks.add(self._post_and_raise_for_status(target, chunk, ignore_errors))

        # Run POST tasks
        result = await gather_with_limited_concurrency(max_num_simultaneous, *tasks)
        statements_count = sum(result)

        logger.debug("Posted %d statements", statements_count)
        return statements_count

    async def _fetch_statements(self, target, raw_output, query_params: dict):
        """Fetch statements from a LRS. Used in `read`."""
        async with AsyncClient(
            auth=self.auth, headers=self.settings.HEADERS.dict(by_alias=True)
        ) as client:
            while True:
                response = await client.get(target, params=query_params)
                response.raise_for_status()
                statements_response = StatementResponse.parse_obj(response.json())
                statements = statements_response.statements
                statements = (
                    [statements] if not isinstance(statements, list) else statements
                )
                if raw_output:
                    for statement in statements:
                        yield bytes(json.dumps(statement), encoding="utf-8")
                else:
                    for statement in statements:
                        yield statement

                if not statements_response.more:
                    break

                query_params.update(parse_qs(urlparse(statements_response.more).query))

    async def _greedy_fetch_statements(self, target, raw_output, query_params: dict):
        """Fetch as many statements as possible and yield when they are available.

        This may be used in the context of paginated results, to allow processing
        of statements while the following page is being fetched. Implementation of
        this function relies on the class method `_fetch_statements`, which must yield
        statements.
        """
        queue = asyncio.Queue()

        async def fetch_all_statements(queue):
            """Fetch all statements and put them in a queue."""
            try:
                async for statement in self._fetch_statements(
                    target=target, raw_output=raw_output, query_params=query_params
                ):
                    await queue.put(statement)
            # Re-raising exceptions is necessary as create_task fails silently
            except Exception as exception:
                # None signals that the queue is done
                await queue.put(None)
                raise exception
            await queue.put(None)

        # Run fetch_all_statements in the background
        task = asyncio.create_task(fetch_all_statements(queue))

        # Yield statements as they arrive
        while True:
            statement = await queue.get()
            if statement is None:
                # Check for exception in fetch_all_statements
                if task.exception():
                    raise task.exception()
                break
            yield statement

    async def _post_and_raise_for_status(self, target, chunk, ignore_errors):
        """POST chunk of statements to `target` and return the number of insertions.

        For use in `write`.
        """
        async with AsyncClient(auth=self.auth, headers=self.settings.HEADERS) as client:
            try:
                request = await client.post(
                    # Encode data to allow async post
                    target,
                    content=json.dumps(list(chunk)).encode("utf-8"),
                )
            except TypeError as error:
                msg = f"Failed to encode JSON: {error}, for document {chunk}"
                logger.error(msg)
                if ignore_errors:
                    return 0
                raise BackendException(msg) from error

            try:
                request.raise_for_status()
                return len(chunk)
            except HTTPError as error:
                msg = "Failed to post statements"
                logger.error("%s. %s", msg, error)
                if ignore_errors:
                    return 0
                raise BackendException(msg, *error.args) from error
