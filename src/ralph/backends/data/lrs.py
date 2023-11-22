"""LRS data backend for Ralph."""

import logging
from io import IOBase
from typing import Iterable, Iterator, List, Optional, Union
from urllib.parse import ParseResult, parse_qs, urljoin, urlparse

from httpx import Client, HTTPError, HTTPStatusError, RequestError
from pydantic import AnyHttpUrl, BaseModel, Field, PositiveInt, parse_obj_as

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    DataBackendStatus,
    Writable,
)
from ralph.backends.lrs.base import LRSStatementsQuery
from ralph.conf import BaseSettingsConfig, HeadersParameters
from ralph.exceptions import BackendException
from ralph.utils import iter_by_batch

logger = logging.getLogger(__name__)


class LRSHeaders(HeadersParameters):
    """Pydantic model for LRS headers."""

    X_EXPERIENCE_API_VERSION: str = Field("1.0.3", alias="X-Experience-API-Version")
    CONTENT_TYPE: str = Field("application/json", alias="content-type")


class LRSDataBackendSettings(BaseDataBackendSettings):
    """LRS data backend default configuration.

    Attributes:
        BASE_URL (AnyHttpUrl): LRS server URL.
        USERNAME (str): Basic auth username for LRS authentication.
        PASSWORD (str): Basic auth password for LRS authentication.
        HEADERS (dict): Headers defined for the LRS server connection.
        LOCALE_ENCODING (str): The encoding used for reading statements.
        READ_CHUNK_SIZE (int): The default chunk size for reading statements.
        STATUS_ENDPOINT (str): Endpoint used to check server status.
        STATEMENTS_ENDPOINT (str): Default endpoint for LRS statements resource.
        WRITE_CHUNK_SIZE (int): The default chunk size for writing statements.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__LRS__"

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


class LRSDataBackend(
    BaseDataBackend[LRSDataBackendSettings, LRSStatementsQuery], Writable
):
    """LRS data backend."""

    name = "lrs"
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
    def client(self) -> Client:
        """Create a `httpx.Client` if it doesn't exist."""
        if not self._client:
            headers = self.settings.HEADERS.dict(by_alias=True)
            self._client = Client(auth=self.auth, headers=headers)
        return self._client

    def status(self) -> DataBackendStatus:
        """HTTP backend check for server status."""
        status_url = urljoin(self.base_url, self.settings.STATUS_ENDPOINT)
        try:
            response = self.client.get(status_url)
            response.raise_for_status()
        except RequestError:
            logger.error("Unable to request the server")
            return DataBackendStatus.AWAY
        except HTTPStatusError:
            logger.error("Response raised an HTTP status of 4xx or 5xx")
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def read(  # noqa: PLR0913
        self,
        query: Optional[LRSStatementsQuery] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
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
            max_statements: The maximum number of statements to yield.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )

    def _read_dicts(
        self,
        query: LRSStatementsQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> Iterator[dict]:
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
            for statement in statements:
                yield statement
        except HTTPError as error:
            msg = "Failed to fetch statements: %s"
            logger.error(msg, error)
            raise BackendException(msg % (error,)) from error

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` records to the `target` endpoint and return their count.

        Args:
            data (Iterable): The data to write.
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
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_dicts(  # noqa: PLR0913
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
            count += self._post_and_raise_for_status(target, chunk, ignore_errors)

        logger.debug("Posted %d statements", count)
        return count

    def close(self) -> None:
        """Close the `httpx.Client`.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            logger.warning("No backend client to close.")
            return

        self.client.close()

    def _fetch_statements(self, target, query_params: dict):
        """Fetch statements from a LRS."""
        while True:
            response = self.client.get(target, params=query_params)
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

    def _post_and_raise_for_status(self, target, chunk, ignore_errors):
        """POST chunk of statements to `target` and return the number of insertions."""
        try:
            request = self.client.post(target, content=chunk)
            request.raise_for_status()
            return len(chunk)
        except HTTPError as error:
            msg = "Failed to post statements: %s"
            if ignore_errors:
                logger.warning(msg, error)
                return 0
            logger.error(msg, error)
            raise BackendException(msg % (error,)) from error
