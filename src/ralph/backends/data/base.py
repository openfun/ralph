"""Base data backend for Ralph."""

import logging
from abc import ABC, abstractmethod
from asyncio import Queue, create_task
from enum import Enum, unique
from functools import cached_property
from io import IOBase
from itertools import chain
from typing import (
    Any,
    AsyncIterator,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, BaseSettings, PositiveInt, ValidationError

from ralph.conf import BaseSettingsConfig, core_settings
from ralph.exceptions import BackendParameterException
from ralph.utils import gather_with_limited_concurrency, iter_by_batch


class BaseDataBackendSettings(BaseSettings):
    """Data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__"
        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING

    LOCALE_ENCODING: str = "utf8"
    READ_CHUNK_SIZE: int = 500
    WRITE_CHUNK_SIZE: int = 500


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


class Loggable:
    """A class with a `logger` and `settings` property."""

    settings: BaseDataBackendSettings

    @cached_property
    def logger(self) -> logging.Logger:
        """Return backend logger."""
        return logging.getLogger(self.__class__.__module__)


class Writable(Loggable, ABC):
    """Data backend interface for backends supporting the write operation."""

    default_operation_type = BaseOperationType.INDEX
    unsupported_operation_types: Set[BaseOperationType] = set()

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
                If `chunk_size` is `None` it defaults to `WRITE_CHUNK_SIZE`.
            ignore_errors (bool): If `True`, escapable errors are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.

        Return:
            int: The number of written records.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        if not operation_type:
            operation_type = self.default_operation_type

        if operation_type in self.unsupported_operation_types:
            msg = f"{operation_type.value.capitalize()} operation_type is not allowed"
            self.logger.error(msg)
            raise BackendParameterException(msg)

        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            self.logger.info("Data Iterator is empty; skipping write to target")
            return 0
        data = chain((first_record,), data)

        chunk_size = chunk_size if chunk_size else self.settings.WRITE_CHUNK_SIZE
        is_bytes = isinstance(first_record, bytes)
        writer = self._write_bytes if is_bytes else self._write_dicts
        return writer(data, target, chunk_size, ignore_errors, operation_type)

    @abstractmethod
    def _write_bytes(  # noqa: PLR0913
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""

    @abstractmethod
    def _write_dicts(  # noqa: PLR0913
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""


class Listable(ABC):
    """Data backend interface for backends supporting the list operation."""

    @abstractmethod
    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
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


Settings = TypeVar("Settings", bound=BaseDataBackendSettings)
Query = TypeVar("Query", bound=BaseQuery)


def validate_backend_query(
    query: Union[str, dict, Query, None],
    query_class: Type[Query],
    logger: logging.Logger,
) -> Query:
    """Validate and transform the backend query."""
    query_name = query_class.__name__
    if query is None:
        try:
            return query_class()
        except ValidationError as error:
            msg = "Invalid %s default query: %s"
            errors = error.errors()
            logger.error(msg, query_name, errors)
            raise BackendParameterException(msg % (query_name, errors)) from error

    if isinstance(query, str):
        try:
            return query_class(query_string=query)
        except ValidationError as error:
            msg = "Invalid %s query string: %s"
            errors = error.errors()
            logger.error(msg, query_name, errors)
            raise BackendParameterException(msg % (query_name, errors)) from error

    if isinstance(query, dict):
        try:
            return query_class(**query)
        except ValidationError as error:
            msg = "The 'query' argument is expected to be a %s instance. %s"
            errors = error.errors()
            logger.error(msg, query_name, errors)
            raise BackendParameterException(msg % (query_name, errors)) from error

    if isinstance(query, query_class):
        return query

    msg = "The 'query' argument is expected to be a %s instance."
    logger.error(msg, query_name)
    raise BackendParameterException(msg % query_name)


class BaseDataBackend(Generic[Settings, Query], Loggable, ABC):
    """Base data backend interface."""

    name = "base"
    query_class: Type[Query]
    settings_class: Type[Settings]

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: D105
        super().__init_subclass__(**kwargs)
        set_backend_settings_class(cls)
        set_backend_query_class(cls)

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the data backend.

        Args:
            settings (Settings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings: Settings = settings if settings else self.settings_class()

    @abstractmethod
    def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, Query]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query: (str or Query): The query to select records to read.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            chunk_size (int or None): The number of records or bytes to read in one
                batch, depending on whether the records are dictionaries or bytes.
                If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
                If the records are dictionaries and `raw_output` is set to `True`, they
                are encoded as JSON.
                If the records are bytes and `raw_output` is set to `False`, they are
                decoded as JSON by line.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default), there is no maximum.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs or
                during encoding records and `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        chunk_size = chunk_size if chunk_size else self.settings.READ_CHUNK_SIZE
        query = validate_backend_query(query, self.query_class, self.logger)
        reader = self._read_bytes if raw_output else self._read_dicts
        statements = reader(query, target, chunk_size, ignore_errors)
        if max_statements is None:
            yield from statements
            return

        if not max_statements:
            return

        max_statements -= 1
        for i, statement in enumerate(statements):
            yield statement
            if i >= max_statements:
                return

    @abstractmethod
    def _read_bytes(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""

    @abstractmethod
    def _read_dicts(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""

    @abstractmethod
    def close(self) -> None:
        """Close the data backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """


class AsyncWritable(Loggable, ABC):
    """Async data backend interface for backends supporting the write operation."""

    default_operation_type = BaseOperationType.INDEX
    unsupported_operation_types: Set[BaseOperationType] = set()

    async def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
        concurrency: Optional[PositiveInt] = None,
    ) -> int:
        """Write `data` records to the `target` container and return their count.

        Args:
            data: (Iterable or IOBase): The data to write.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            chunk_size (int or None): The number of records or bytes to write in one
                batch, depending on whether `data` contains dictionaries or bytes.
                If `chunk_size` is `None` it defaults to `WRITE_CHUNK_SIZE`.
            ignore_errors (bool): If `True`, escapable errors are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.
            concurrency (int): The number of chunks to write concurrently.
                If `None` it defaults to `1`.

        Return:
            int: The number of written records.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        if not operation_type:
            operation_type = self.default_operation_type

        if operation_type in self.unsupported_operation_types:
            msg = f"{operation_type.value.capitalize()} operation_type is not allowed"
            self.logger.error(msg)
            raise BackendParameterException(msg)

        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            self.logger.info("Data Iterator is empty; skipping write to target")
            return 0
        data = chain((first_record,), data)

        chunk_size = chunk_size if chunk_size else self.settings.WRITE_CHUNK_SIZE
        is_bytes = isinstance(first_record, bytes)
        writer = self._write_bytes if is_bytes else self._write_dicts

        concurrency = concurrency if concurrency else 1
        if concurrency == 1:
            return await writer(data, target, chunk_size, ignore_errors, operation_type)

        if concurrency < 1:
            msg = "concurrency must be a strictly positive integer"
            self.logger.error(msg)
            raise BackendParameterException(msg)

        count = 0
        for batch in iter_by_batch(iter_by_batch(data, chunk_size), concurrency):
            tasks = set()
            for chunk in batch:
                task = writer(chunk, target, chunk_size, ignore_errors, operation_type)
                tasks.add(task)
            result = await gather_with_limited_concurrency(concurrency, *tasks)
            count += sum(result)
        return count

    @abstractmethod
    async def _write_bytes(  # noqa: PLR0913
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""

    @abstractmethod
    async def _write_dicts(  # noqa: PLR0913
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""


class AsyncListable(ABC):
    """Async data backend interface for backends supporting the list operation."""

    @abstractmethod
    async def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[AsyncIterator[str], AsyncIterator[dict]]:
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


class BaseAsyncDataBackend(Generic[Settings, Query], Loggable, ABC):
    """Base async data backend interface."""

    name = "base"
    query_class: Type[Query]
    settings_class: Type[Settings]

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: D105
        super().__init_subclass__(**kwargs)
        set_backend_settings_class(cls)
        set_backend_query_class(cls)

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the data backend.

        Args:
            settings (Settings or None): The backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings: Settings = settings if settings else self.settings_class()

    @abstractmethod
    async def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    async def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, Query]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        prefetch: Optional[int] = None,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[AsyncIterator[bytes], AsyncIterator[dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query: (str or Query): The query to select records to read.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            chunk_size (int or None): The number of records or bytes to read in one
                batch, depending on whether the records are dictionaries or bytes.
                If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
                If the records are dictionaries and `raw_output` is set to `True`, they
                are encoded as JSON.
                If the records are bytes and `raw_output` is set to `False`, they are
                decoded as JSON by line.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            prefetch: The number of records to prefetch (queue) while yielding.
                If `prefetch` is `None` or `0` it defaults to `1` - no records are
                prefetched.
                If `prefetch` is less than zero, all records are prefetched.
                Caution: setting `prefetch<0` might potentially lead to large amounts
                of API calls and to the memory filling up.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default), there is no maximum.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs or
                during encoding records and `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        if prefetch and prefetch != 1:
            queue = Queue(prefetch - 1)
            statements = self.read(
                query,
                target,
                chunk_size,
                raw_output,
                ignore_errors,
                None,
                max_statements,
            )
            task = create_task(self._queue_records(queue, statements))
            while True:
                statement = await queue.get()
                if statement is None:
                    error = task.exception()
                    if error:
                        raise error

                    break

                yield statement

            return

        chunk_size = chunk_size if chunk_size else self.settings.READ_CHUNK_SIZE
        query = validate_backend_query(query, self.query_class, self.logger)
        reader = self._read_bytes if raw_output else self._read_dicts
        statements = reader(query, target, chunk_size, ignore_errors)
        if max_statements is None:
            async for statement in statements:
                yield statement
            return

        if not max_statements:
            return

        i = 0
        async for statement in statements:
            yield statement
            i += 1
            if i >= max_statements:
                return

    @abstractmethod
    async def _read_bytes(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> AsyncIterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""

    @abstractmethod
    async def _read_dicts(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> AsyncIterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""

    @abstractmethod
    async def close(self) -> None:
        """Close the data backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """

    async def _queue_records(
        self, queue: Queue, records: Union[AsyncIterator[bytes], AsyncIterator[dict]]
    ):
        """Iterate over the `records` and put them into the `queue`."""
        try:
            async for record in records:
                await queue.put(record)
        except Exception as error:
            # None signals that the queue is done
            await queue.put(None)
            raise error

        await queue.put(None)


def get_backend_generic_argument(
    backend_class: Type[Union[BaseDataBackend, BaseAsyncDataBackend]], position: int
) -> Optional[Type]:
    """Return the generic argument of `backend_class` at specified `position`."""
    if not hasattr(backend_class, "__orig_bases__"):
        return None

    bases = backend_class.__orig_bases__[0]
    if not hasattr(bases, "__args__") or len(bases.__args__) < abs(position) + 1:
        return None

    argument = bases.__args__[position]
    if argument is Any:
        return None

    if isinstance(argument, TypeVar):
        return argument.__bound__

    if isinstance(argument, Type):
        return argument

    return None


def set_backend_settings_class(
    backend_class: Type[Union[BaseDataBackend, BaseAsyncDataBackend]]
) -> None:
    """Set `settings_class` attribute with `Config.env_prefix` for `backend_class`."""
    settings_class = get_backend_generic_argument(backend_class, 0)
    if settings_class:
        backend_class.settings_class = settings_class


def set_backend_query_class(
    backend_class: Type[Union[BaseDataBackend, BaseAsyncDataBackend]]
) -> None:
    """Set `query_class` attribute for `backend_class`."""
    query_class = get_backend_generic_argument(backend_class, 1)
    if query_class:
        backend_class.query_class = query_class
