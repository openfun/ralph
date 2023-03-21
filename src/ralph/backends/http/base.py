"""Base HTTP backend for Ralph."""

import functools
import logging
from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import Iterator, List, Optional, Union

from pydantic import BaseModel, ValidationError

from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


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
    """Enforces query argument type checking for methods using it."""

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


class BaseHTTP(ABC):
    """Base HTTP backend interface."""

    name = "base"
    query = BaseQuery

    def validate_query(self, query: Union[str, dict, BaseQuery] = None) -> BaseQuery:
        """Validates and transforms the query."""
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
    def list(
        self, target: str = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """Lists containers in the data backend. E.g., collections, files, indexes."""

    @abstractmethod
    def status(self) -> HTTPBackendStatus:
        """Implements HTTP backend check for server status."""

    @abstractmethod
    @enforce_query_checks
    def read(  # pylint: disable=too-many-arguments
        self,
        query: Union[str, BaseQuery] = None,
        target: str = None,
        chunk_size: Union[None, int] = 500,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Yields records read from the HTTP response results."""

    @abstractmethod
    def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[List[bytes], List[dict]],
        target: Union[None, str] = None,
        chunk_size: Union[None, int] = 500,
        ignore_errors: bool = False,
        operation_type: Union[None, OperationType] = None,
    ) -> int:
        """Writes statements into the HTTP server given an input endpoint."""
