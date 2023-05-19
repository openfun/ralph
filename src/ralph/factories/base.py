"""Base data backend for Ralph."""

import functools
import logging
from abc import ABC, abstractmethod
from enum import Enum, unique
from io import IOBase
from typing import Iterable, Iterator, Optional, Union

from pydantic import BaseModel, BaseSettings, ValidationError

from ralph.conf import BaseSettingsConfig, core_settings
from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


class BaseDataBackendSettings(BaseSettings):
    """Represents the data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__"
        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING


class BaseQuery(BaseModel):
    """Base query model."""

    class Config:
        """Base query model configuration."""

        extra = "forbid"

    query_string: Optional[str]


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
    """Enforces query argument type checking for methods using it."""

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
    settings_class = BaseDataBackendSettings

    @abstractmethod
    def __init__(self, settings: settings_class = None):
        """Instantiates the data backend.

        Args:
            settings (BaseDataBackendSettings or None): The backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """

    def validate_query(self, query: Union[str, dict, BaseQuery] = None) -> BaseQuery:
        """Validates and transforms the query."""
        if query is None:
            query = self.query_model()

        if isinstance(query, str):
            query = self.query_model(query_string=query)

        if isinstance(query, dict):
            try:
                query = self.query_model(**query)
            except ValidationError as err:
                raise BackendParameterException(
                    "The 'query' argument is expected to be a "
                    f"{self.query_model.__name__} instance. {err.errors()}"
                ) from err

        if not isinstance(query, self.query_model):
            raise BackendParameterException(
                "The 'query' argument is expected to be a "
                f"{self.query_model.__name__} instance."
            )

        logger.debug("Query: %s", str(query))

        return query

    @abstractmethod
    def status(self) -> DataBackendStatus:
        """Implements data backend checks (e.g. connection, cluster status).

        Returns:
            DataBackendStatus: The status of the data backend.
        """

    @abstractmethod
    def list(
        self, target: str = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """Lists containers in the data backend. E.g., collections, files, indexes.

        Args:
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            details (bool): Get detailed container information instead of just names.
            new (bool): Given the history, list only not already read containers.

        Yields:
            str: If `details` is False.
            dict: If `details` is True.

        Raises:
            BackendException: If a failure occurs.
            BackendParameterException: If a backend argument value is not valid.
        """

    @abstractmethod
    @enforce_query_checks
    def read(
        self,
        *,
        query: Union[str, BaseQuery] = None,
        target: str = None,
        chunk_size: Union[None, int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Reads records matching the `query` in the `target` container and yields them.

        Args:
            query: (str or BaseQuery): The query to select records to read.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
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

        Yields:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raises:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """

    @abstractmethod
    def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[None, str] = None,
        chunk_size: Union[None, int] = None,
        ignore_errors: bool = False,
        operation_type: Union[None, BaseOperationType] = None,
    ) -> int:
        """Writes `data` records to the `target` container and returns their count.

        Args:
            data: (Iterable or IOBase): The data to write.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            chunk_size (int or None): The number of records or bytes to write in one
                batch, depending on whether `data` contains dictionaries or bytes.
                If `chunk_size` is `None`, a default value is used instead.
            ignore_errors (bool): If `True`, errors during the write operation
                are ignored and logged. If `False` (default), a `BackendException`
                is raised if an error occurs.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.

        Returns:
            int: The number of written records.

        Raises:
            BackendException: If a failure during the write operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
