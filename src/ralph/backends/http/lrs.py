"""LRS HTTP backend for Ralph."""

import json
import logging
from itertools import chain
from typing import Iterable, Iterator, List, Optional, Union
from urllib.parse import ParseResult, parse_qs, urljoin, urlparse

import httpx
from httpx import Client, HTTPError, HTTPStatusError, RequestError
from more_itertools import chunked
from pydantic import AnyHttpUrl, BaseModel, parse_obj_as

from ralph.conf import LRSHeaders, settings
from ralph.exceptions import BackendException, BackendParameterException

from .base import (
    BaseHTTP,
    BaseQuery,
    HTTPBackendStatus,
    OperationType,
    enforce_query_checks,
)

lrs_settings = settings.BACKENDS.HTTP.LRS
logger = logging.getLogger(__name__)


class StatementResponse(BaseModel):
    """Pydantic model for `get` statements response."""

    statements: Union[List[dict], dict]
    more: Optional[str]


class LRSQuery(BaseQuery):
    """LRS body query model."""

    query: Optional[dict]


class LRSHTTP(BaseHTTP):
    """LRS HTTP backend."""

    name = "lrs"
    query = LRSQuery
    default_operation_type = OperationType.CREATE

    def __init__(  # pylint: disable=too-many-arguments
        self,
        base_url: str = lrs_settings.BASE_URL,
        username: str = lrs_settings.USERNAME,
        password: str = lrs_settings.PASSWORD,
        headers: LRSHeaders = lrs_settings.HEADERS,
        status_endpoint: str = lrs_settings.STATUS_ENDPOINT,
        statements_endpoint: str = lrs_settings.STATEMENTS_ENDPOINT,
    ):
        """Instantiates the LRS client.

        Args:
            base_url (AnyHttpUrl): LRS server URL.
            username (str): Basic auth username for LRS authentication.
            password (str): Basic auth password for LRS authentication.
            headers (dict): Headers defined for the LRS server connection.
            status_endpoint (str): Endpoint used to check server status.
            statements_endpoint (str): Default endpoint for LRS statements resource.
        """
        self.base_url = parse_obj_as(AnyHttpUrl, base_url)
        self.auth = (username, password)
        self.headers = headers
        self.status_endpoint = status_endpoint
        self.statements_endpoint = statements_endpoint

    def status(self):
        """Implements HTTP backend check for server status."""
        status_url = urljoin(self.base_url, self.status_endpoint)

        try:
            response = httpx.get(status_url)
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

    def list(
        self, target: str = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        # noqa: D205, D415
        """LRS HTTP backend does not support `list` method,
        calling this method will raise an error.
        """
        msg = "LRS HTTP backend does not support `list` method, cannot list from %s"
        logger.error(msg, target)
        raise NotImplementedError(msg % target)

    @enforce_query_checks
    def read(  # pylint: disable=too-many-arguments
        self,
        query: Union[str, LRSQuery] = None,
        target: str = None,
        chunk_size: Union[None, int] = 500,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Get statements from LRS `target` endpoint.

        The `read` method defined in the LRS specification returns `statements` array
        and `more` IRL. The latter is required when the returned `statement` list has
        been limited.

        Args:
            query (str, LRSQuery):  The query to select records to read.
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
                are be ignored and logged. If `False` (default), a `BackendException`
                is raised if an error occurs.
        """
        if not target:
            target = self.statements_endpoint

        query_params = {}
        if query.query:
            query_params.update(query.query)

        # Set chunk_size to limit parameter if not exist in the query
        query_params.setdefault("limit", chunk_size)

        # Create request URL
        target = ParseResult(
            scheme=urlparse(self.base_url).scheme,
            netloc=urlparse(self.base_url).netloc,
            path=target,
            query="",
            params="",
            fragment="",
        ).geturl()

        def fetch_statements(params: dict):
            while True:
                with Client(auth=self.auth, headers=self.headers) as client:
                    response = client.get(target, params=params)
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

                    params.update(parse_qs(urlparse(statements_response.more).query))

        try:
            yield from fetch_statements(params=query_params)
        except HTTPError as error:
            msg = "Failed to fetch statements."
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error

    def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[Iterable[bytes], Iterable[dict]],
        target: Union[None, str] = None,
        chunk_size: Union[None, int] = 500,
        ignore_errors: bool = False,
        operation_type: Union[None, OperationType] = None,
    ) -> int:
        """Writes `data` records to the `target` endpoint and returns their count.

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
        """
        statements_count = 0

        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.debug("Data Iterator is empty; skipping write to target.")
            return statements_count

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
            target = self.statements_endpoint

        target = ParseResult(
            scheme=urlparse(self.base_url).scheme,
            netloc=urlparse(self.base_url).netloc,
            path=target,
            query="",
            params="",
            fragment="",
        ).geturl()

        data = chain((first_record,), data)
        if isinstance(first_record, dict):
            data = self._parse_dict_to_bytes(data, ignore_errors)

        logger.debug(
            "Start writing to the %s endpoint (chunk size: %d)", target, chunk_size
        )

        with Client(auth=self.auth, headers=self.headers) as client:
            for chunk in chunked(data, chunk_size):
                request = client.post(target, content=chunk)
                try:
                    request.raise_for_status()
                except HTTPError as error:
                    msg = "Failed to post statements"
                    logger.error("%s. %s", msg, error)
                    raise BackendException(msg, *error.args) from error
                statements_count += len(chunk)
                logger.info("Posted %d statements", statements_count)

        return statements_count

    @staticmethod
    def _parse_dict_to_bytes(
        statements: Iterable[dict], ignore_errors: bool
    ) -> Iterator[bytes]:
        """Reads the `statements` Iterable and yields dictionaries."""
        for statement in statements:
            try:
                yield bytes(json.dumps(statement), encoding="utf-8")
            except TypeError as error:
                msg = "Failed to encode JSON: %s, for document %s"
                logger.error(msg, error, statement)
                if ignore_errors:
                    continue
                raise BackendException(msg % (error, statement)) from error
