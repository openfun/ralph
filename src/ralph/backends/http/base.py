"""Base HTTP backend for Ralph."""

import functools
import logging
from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import Iterator, List, Optional, Union

from pydantic import BaseModel, BaseSettings, ValidationError
from pydantic.types import PositiveInt

from ralph.conf import BaseSettingsConfig, core_settings
from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


class BaseHTTPBackendSettings(BaseSettings):
    """Data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__HTTP__"
        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING


@unique
class HTTPBackendStatus(Enum):
    """HTTP backend statuses."""

    OK = "ok"
    AWAY = "away"
    ERROR = "error"


class OperationType(Enum):
    """Data backend operation types.

    Attributes:
        INDEX (str): creates a new record with a specific ID.
        CREATE (str): creates a new record without a specific ID.
        DELETE (str): deletes an existing record.
        UPDATE (str): updates or overwrites an existing record.
        APPEND (str): creates or appends data to an existing record.
    """

    INDEX = "index"
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    APPEND = "append"


def enforce_query_checks(method):
    """Enforce query argument type checking for methods using it."""

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        """Wrap method execution."""
        query = kwargs.pop("query", None)
        self_ = args[0]

        return method(*args, query=self_.validate_query(query), **kwargs)

    return wrapper


class BaseQuery(BaseModel):
    """Base query model."""

    class Config:
        """Base query model configuration."""

        extra = "forbid"

    query_string: Optional[str]


class BaseHTTPBackend(ABC):
    """Base HTTP backend interface."""

    name = "base"
    query = BaseQuery

    def validate_query(
        self, query: Optional[Union[str, dict, BaseQuery]] = None
    ) -> BaseQuery:
        """Validate and transforms the query."""
        if query is None:
            query = self.query()

        if isinstance(query, str):
            query = self.query(query_string=query)

        if isinstance(query, dict):
            try:
                query = self.query(**query)
            except ValidationError as err:
                raise BackendParameterException(
                    "The 'query' argument is expected to be a "
                    f"{self.query.__name__} instance. {err.errors()}"
                ) from err

        if not isinstance(query, self.query):
            raise BackendParameterException(
                "The 'query' argument is expected to be a "
                f"{self.query.__name__} instance."
            )

        logger.debug("Query: %s", str(query))

        return query

    @abstractmethod
    async def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List containers in the data backend. E.g., collections, files, indexes."""

    @abstractmethod
    async def status(self) -> HTTPBackendStatus:
        """Implement HTTP backend check for server status."""

    @abstractmethod
    @enforce_query_checks
    async def read(  # pylint: disable=too-many-arguments
        self,
        query: Optional[Union[str, BaseQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[PositiveInt] = 500,
        raw_output: bool = False,
        ignore_errors: bool = False,
        greedy: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Iterator[Union[bytes, dict]]:
        """Yield records read from the HTTP response results."""

    @abstractmethod
    async def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[List[bytes], List[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[PositiveInt] = 500,
        ignore_errors: bool = False,
        operation_type: Optional[OperationType] = None,
        simultaneous: bool = False,
        max_num_simultaneous: Optional[int] = None,
    ) -> int:
        """Write statements into the HTTP server given an input endpoint."""
