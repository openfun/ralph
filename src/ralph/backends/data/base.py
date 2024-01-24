"""Base data backend for Ralph."""

import logging
from abc import ABC, abstractmethod
from asyncio import Queue, create_task
from enum import Enum, IntEnum, unique
from inspect import isclass
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
    get_args,
    get_origin,
)

from pydantic import BaseModel, BaseSettings, PositiveInt, ValidationError
from typing_extensions import Self, get_original_bases

from ralph.conf import BaseSettingsConfig, core_settings
from ralph.exceptions import BackendParameterException
from ralph.utils import (
    async_parse_dict_to_bytes,
    async_parse_iterable_to_dict,
    gather_with_limited_concurrency,
    iter_by_batch,
    parse_dict_to_bytes,
    parse_iterable_to_dict,
)

logger = logging.getLogger(__name__)


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

    @classmethod
    def from_string(cls, query: str) -> Self:
        """Return an instance of BaseQuery from a string."""
        try:
            return cls.parse_raw(query)
        except ValidationError as error:
            msg = "Invalid %s query string: %s"
            errors = error.errors()
            logger.error(msg, cls.__name__, errors)
            raise BackendParameterException(msg % (cls.__name__, errors)) from error


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


class Configurable:
    """A class that is configurable via data backend settings."""

    settings: BaseDataBackendSettings


class Writable(Configurable, ABC):
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
            data (Iterable or IOBase): The data to write.
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
            logger.error(msg)
            raise BackendParameterException(msg)

        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target")
            return 0
        data = chain((first_record,), data)

        chunk_size = chunk_size if chunk_size else self.settings.WRITE_CHUNK_SIZE
        is_bytes = isinstance(first_record, bytes)
        writer = self._write_bytes if is_bytes else self._write_dicts
        return writer(data, target, chunk_size, ignore_errors, operation_type)

    def _write_bytes(  # noqa: PLR0913
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        statements = parse_iterable_to_dict(data, ignore_errors)
        return self._write_dicts(
            statements, target, chunk_size, ignore_errors, operation_type
        )

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
        locale = self.settings.LOCALE_ENCODING
        statements = parse_dict_to_bytes(data, locale, ignore_errors)
        return self._write_bytes(
            statements, target, chunk_size, ignore_errors, operation_type
        )


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
Query = TypeVar("Query", bound=Union[BaseQuery, str])


def validate_backend_query(
    query: Optional[Query],
    query_class: Type[Query],
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

    if isinstance(query, query_class):
        return query

    msg = "The 'query' argument is expected to be a %s instance"
    logger.error(msg, query_name)
    raise BackendParameterException(msg % query_name)


class DataBackendArgument(IntEnum):
    """Enumerate data backend generic arguments."""

    SETTINGS = 0
    QUERY = 1


class BaseDataBackend(Generic[Settings, Query], ABC):
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
        try:
            self.settings: Settings = settings if settings else self.settings_class()
        except ValidationError as error:
            msg = "Failed to instantiate default data backend settings: %s"
            logger.error(msg, error)
            raise BackendParameterException(msg % error) from error

    @abstractmethod
    def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    def read(  # noqa: PLR0913
        self,
        query: Optional[Query] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query (Query): The query to select records to read.
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
                If `None` (default) or `0`, there is no maximum.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs or
                during encoding records and `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        chunk_size = chunk_size if chunk_size else self.settings.READ_CHUNK_SIZE
        query = validate_backend_query(query, self.query_class)
        reader = self._read_bytes if raw_output else self._read_dicts
        statements = reader(query, target, chunk_size, ignore_errors)
        if not max_statements:
            yield from statements
            return

        max_statements -= 1
        for i, statement in enumerate(statements):
            yield statement
            if i >= max_statements:
                return

    def _read_bytes(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        locale = self.settings.LOCALE_ENCODING
        statements = self._read_dicts(query, target, chunk_size, ignore_errors)
        yield from parse_dict_to_bytes(statements, locale, ignore_errors)

    @abstractmethod
    def _read_dicts(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        statements = self._read_bytes(query, target, chunk_size, ignore_errors)
        yield from parse_iterable_to_dict(statements, ignore_errors)

    @abstractmethod
    def close(self) -> None:
        """Close the data backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """


class AsyncWritable(Configurable, ABC):
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
            data (Iterable or IOBase): The data to write.
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
            logger.error(msg)
            raise BackendParameterException(msg)

        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target")
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
            logger.error(msg)
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
        locale = self.settings.LOCALE_ENCODING
        statements = parse_dict_to_bytes(data, locale, ignore_errors)
        return await self._write_bytes(
            statements, target, chunk_size, ignore_errors, operation_type
        )


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


class BaseAsyncDataBackend(Generic[Settings, Query], ABC):
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
        try:
            self.settings: Settings = settings if settings else self.settings_class()
        except ValidationError as error:
            msg = "Failed to instantiate default async data backend settings: %s"
            logger.error(msg, error)
            raise BackendParameterException(msg % error) from error

    @abstractmethod
    async def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    async def read(  # noqa: PLR0913
        self,
        query: Optional[Query] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        prefetch: Optional[PositiveInt] = None,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[AsyncIterator[bytes], AsyncIterator[dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query (Query): The query to select records to read.
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
            prefetch (int): The number of records to prefetch (queue) while yielding.
                If `prefetch` is `None` it defaults to `1`, i.e. no records are
                prefetched.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default) or `0`, there is no maximum.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs or
                during encoding records and `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        prefetch = prefetch if prefetch else 1
        if prefetch < 1:
            msg = "prefetch must be a strictly positive integer"
            logger.error(msg)
            raise BackendParameterException(msg)

        if prefetch > 1:
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

                    return

                yield statement

        chunk_size = chunk_size if chunk_size else self.settings.READ_CHUNK_SIZE
        query = validate_backend_query(query, self.query_class)
        reader = self._read_bytes if raw_output else self._read_dicts
        statements = reader(query, target, chunk_size, ignore_errors)
        if not max_statements:
            async for statement in statements:
                yield statement
            return

        i = 0
        async for statement in statements:
            yield statement
            i += 1
            if i >= max_statements:
                return

    async def _read_bytes(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> AsyncIterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        statements = self._read_dicts(query, target, chunk_size, ignore_errors)
        async for statement in async_parse_dict_to_bytes(
            statements, self.settings.LOCALE_ENCODING, ignore_errors
        ):
            yield statement

    @abstractmethod
    async def _read_dicts(
        self, query: Query, target: Optional[str], chunk_size: int, ignore_errors: bool
    ) -> AsyncIterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        statements = self._read_bytes(query, target, chunk_size, ignore_errors)
        statements = async_parse_iterable_to_dict(statements, ignore_errors)
        async for statement in statements:
            yield statement

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


DataBackend = TypeVar("DataBackend", BaseDataBackend, BaseAsyncDataBackend)


def get_backend_generic_argument(
    backend_class: Type[DataBackend],
    position: DataBackendArgument,
) -> Optional[Type]:
    """Return the generic argument of `backend_class` at specified `position`."""
    for base in get_original_bases(backend_class):
        origin = get_origin(base)
        if not (
            origin
            and isclass(origin)
            and issubclass(origin, (BaseDataBackend, BaseAsyncDataBackend))
        ):
            continue

        args = get_args(base)
        if len(args) < abs(position) + 1:
            return None

        argument = args[position]
        if argument is Any:
            return None

        if isinstance(argument, TypeVar):
            argument = argument.__bound__

        if get_origin(argument) is Union:
            argument = get_args(argument)[0]

        if isinstance(argument, Type):
            return argument

    return None


def set_backend_settings_class(backend_class: Type[DataBackend]) -> None:
    """Set `settings_class` attribute with `Config.env_prefix` for `backend_class`."""
    settings_class = get_backend_generic_argument(
        backend_class, DataBackendArgument.SETTINGS
    )
    if settings_class:
        backend_class.settings_class = settings_class


def set_backend_query_class(backend_class: Type[DataBackend]) -> None:
    """Set `query_class` attribute for `backend_class`."""
    query_class = get_backend_generic_argument(backend_class, DataBackendArgument.QUERY)
    if query_class:
        backend_class.query_class = query_class
