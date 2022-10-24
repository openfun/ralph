"""Base data backend for Ralph."""

import functools
import logging
from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import Generator, Iterable, Union

from pydantic import BaseModel, BaseSettings

from ralph.conf import BaseSettingsConfig, settings
from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


class BaseDataBackendSettings(BaseSettings):
    """Represent the data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__"
        env_file = ".env"
        env_file_encoding = settings.LOCALE_ENCODING


class BaseQuery(BaseModel):
    """Base query model."""

    class Config:
        """Base query model configuration."""

        extra = "forbid"

    query_string: Union[str, None] = None


@unique
class BaseOperationType(Enum):
    """Base data backend operation types.

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


@unique
class DataBackendStatus(Enum):
    """Data backend statuses."""

    OK = "ok"
    AWAY = "away"
    ERROR = "error"


def enforce_query_checks(method):
    """Enforce query argument type checking for methods using it."""

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        """Wrap method execution."""

        query = kwargs.pop("query", None)
        self_ = args[0]

        return method(*args, query=self_.validate_query(query), **kwargs)

    return wrapper


class BaseDataBackend(ABC):
    """Base data backend interface."""

    name = "base"
    query_model = BaseQuery
    default_operation_type = BaseOperationType.INDEX
    settings = BaseDataBackendSettings()

    def validate_query(self, query: Union[str, BaseQuery] = None) -> BaseQuery:
        """Validates and transforms the query."""

        if query is None:
            query = self.query_model()

        if isinstance(query, str):
            query = self.query_model(query_string=query)

        if not isinstance(query, self.query_model):
            raise BackendParameterException(
                "The 'query' argument is expected to be a "
                f"{self.query_model().__class__.__name__} instance."
            )

        logger.debug("Query: %s", str(query))

        return query

    @abstractmethod
    def status(self) -> DataBackendStatus:
        """Implements data backend checks (e.g. connection, cluster status)."""

    @abstractmethod
    def list(
        self, target: str = None, details: bool = False, new: bool = False
    ) -> Generator[None, Union[str, dict], None]:
        """Lists containers in the data backend. E.g., collections, files, indexes.

        Yields:
            str: If `details` is False.
            dict: If `details` is True.
        """

    @abstractmethod
    @enforce_query_checks
    def read(
        self,
        *,
        query: Union[str, BaseQuery] = None,
        target: str = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
    ) -> Generator[None, Union[bytes, dict], None]:
        """Reads records matching the query in the target container and yields them.

        Yields:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.
        """

    @abstractmethod
    def write(  # pylint: disable=too-many-arguments
        self,
        stream: Iterable[Union[bytes, str, dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
    ) -> int:
        """Writes stream records to the target container and returns their count."""
