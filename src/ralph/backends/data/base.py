"""Base data backend for Ralph."""

import logging
from abc import ABC, abstractmethod
from enum import Enum, unique
from io import IOBase
from typing import Iterable, Iterator, Optional, Union

from pydantic import BaseSettings

from ralph.conf import BaseSettingsConfig, core_settings

logger = logging.getLogger(__name__)


class BaseDataBackendSettings(BaseSettings):
    """Data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__"
        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING


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


class Writable(ABC):
    """Data backend interface for backends supporting the write operation."""

    default_operation_type = BaseOperationType.INDEX

    @abstractmethod
    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` records to the `target` container and return their count.

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

        Return:
            int: The number of written records.

        Raise:
            BackendException: If a failure during the write operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """


class Listable(ABC):
    """Data backend interface for backends supporting the list operation."""

    @abstractmethod
    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List containers in the data backend. E.g., collections, files, indexes.

        Args:
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            details (bool): Get detailed container information instead of just names.
            new (bool): Given the history, list only not already read containers.

        Yield:
            str: If `details` is False.
            dict: If `details` is True.

        Raise:
            BackendException: If a failure occurs.
            BackendParameterException: If a backend argument value is not valid.
        """


class BaseDataBackend(ABC):
    """Base data backend interface."""

    name = "base"
    query_class = None
    settings_class = BaseDataBackendSettings

    @abstractmethod
    def __init__(self, settings: Optional[BaseDataBackendSettings] = None):
        """Instantiate the data backend.

        Args:
            settings (BaseDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """

    @abstractmethod
    def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    @abstractmethod
    def read(  # noqa: PLR0913
        self,
        *,
        query: Optional[str] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query: (str): The query to select records to read.
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

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """

    @abstractmethod
    def close(self) -> None:
        """Close the data backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """


class AsyncWritable(ABC):
    """Async data backend interface for backends supporting the write operation."""

    default_operation_type = BaseOperationType.INDEX

    @abstractmethod
    async def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` records to the `target` container and return their count.

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

        Return:
            int: The number of written records.

        Raise:
            BackendException: If a failure during the write operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """


class AsyncListable(ABC):
    """Async data backend interface for backends supporting the list operation."""

    @abstractmethod
    async def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List containers in the data backend. E.g., collections, files, indexes.

        Args:
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            details (bool): Get detailed container information instead of just names.
            new (bool): Given the history, list only not already read containers.

        Yield:
            str: If `details` is False.
            dict: If `details` is True.

        Raise:
            BackendException: If a failure occurs.
            BackendParameterException: If a backend argument value is not valid.
        """


class BaseAsyncDataBackend(ABC):
    """Base async data backend interface."""

    name = "base"
    query_class = None
    settings_class = BaseDataBackendSettings

    @abstractmethod
    def __init__(self, settings: Optional[BaseDataBackendSettings] = None):
        """Instantiate the data backend.

        Args:
            settings (BaseDataBackendSettings or None): The backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """

    @abstractmethod
    async def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    @abstractmethod
    async def read(  # noqa: PLR0913
        self,
        *,
        query: Optional[str] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query: (str): The query to select records to read.
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

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close the data backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
