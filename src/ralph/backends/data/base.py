"""Base data backend for Ralph."""

import functools
import logging
from abc import abstractmethod
from enum import Enum, unique
from io import IOBase
from itertools import chain
from typing import Iterable, Iterator, Set, Type, Union

from pydantic import BaseModel, ValidationError

from ralph.backends.base import (
    BaseBackend,
    BaseBackendSettings,
    BaseBackendSettingsConfig,
)
from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


class BaseDataBackendSettings(BaseBackendSettings):
    """Data backend default configuration."""

    class Config(BaseBackendSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__"

    DEFAULT_CHUNK_SIZE: int = 500
    LOCALE_ENCODING: str = "utf8"


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


def validate_backend_query(
    query: Union[str, dict, BaseQuery, None],
    query_class: Type[BaseQuery],
    logger_: logging.Logger,
) -> BaseQuery:
    """Validate and transform the backend query."""
    if query is None:
        return query_class()

    if isinstance(query, str):
        return query_class(query_string=query)

    if isinstance(query, dict):
        try:
            return query_class(**query)
        except ValidationError as error:
            msg = "The 'query' argument is expected to be a %s instance. %s"
            name = query_class.__name__
            errors = error.errors()
            logger_.error(msg, name, errors)
            raise BackendParameterException(msg % (name, errors)) from error

    if isinstance(query, query_class):
        return query

    msg = "The 'query' argument is expected to be a %s instance."
    logger_.error(msg, query_class.__name__)
    raise BackendParameterException(msg % (query_class.__name__,))


# Replaced by `validate_backend_query`
def enforce_query_checks(method):
    """Enforce query argument type checking for methods using it."""

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        """Wrap method execution."""
        query = kwargs.pop("query", None)
        self_ = args[0]

        return method(*args, query=self_.validate_query(query), **kwargs)

    return wrapper


class BaseDataBackend(BaseBackend):
    """Base data backend interface."""

    type = "data"
    name = "base"
    logger = logger
    query_class = BaseQuery  # we rename query_model to query_class
    query_model = BaseQuery
    default_operation_type: BaseOperationType = BaseOperationType.INDEX
    unsupported_operation_types: Set[BaseOperationType] = set()
    settings_class = BaseDataBackendSettings
    settings: settings_class

    # This method is replaced by validate_backend_query
    def validate_query(
        self, query: Union[str, dict, BaseQuery, None] = None
    ) -> BaseQuery:
        """Validate and transform the query."""
        if query is None:
            query = self.query_model()

        if isinstance(query, str):
            query = self.query_model(query_string=query)

        if isinstance(query, dict):
            try:
                query = self.query_model(**query)
            except ValidationError as error:
                msg = "The 'query' argument is expected to be a %s instance. %s"
                errors = error.errors()
                logger.error(msg, self.query_model.__name__, errors)
                raise BackendParameterException(
                    msg % (self.query_model.__name__, errors)
                ) from error

        if not isinstance(query, self.query_model):
            msg = "The 'query' argument is expected to be a %s instance."
            logger.error(msg, self.query_model.__name__)
            raise BackendParameterException(msg % (self.query_model.__name__,))

        logger.debug("Query: %s", str(query))

        return query

    @abstractmethod
    def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    @abstractmethod
    def list(
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
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

    def read(
        self,
        *,  # We could allow positional arguments once we use validate_backend_query
        query: Union[str, dict, query_class, None] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        # (uncomment once all backends use the pattern)
        # max_statements: Union[int, None] = None,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read records matching the `query` in the `target` container and yield them.

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
            max_statements: The maximum number of statements to yield.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        chunk_size = chunk_size if chunk_size else self.settings.DEFAULT_CHUNK_SIZE
        query = validate_backend_query(query, self.query_class, self.logger)
        reader = self._read_bytes if raw_output else self._read_dicts
        # pylint: disable=assignment-from-no-return
        # NB: this pylint warning goes away once the methods are abstract
        statements = reader(query, target, chunk_size, ignore_errors)
        yield from statements
        # (uncomment once all backends use the pattern)
        # if max_statements is None:
        #     yield from statements
        #     return
        # for i, statement in enumerate(statements):
        #     if i >= max_statements:
        #         return
        #     yield statement

    # @abstractmethod (uncomment once all backends use the pattern)
    def _read_bytes(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""

    # @abstractmethod (uncomment once all backends use the pattern)
    def _read_dicts(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""

    def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
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
        if not operation_type:
            operation_type = self.default_operation_type
        if operation_type in self.unsupported_operation_types:
            msg = f"{operation_type.value.capitalize()} operation_type is not allowed."
            self.logger.error(msg)
            raise BackendParameterException(msg)

        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            self.logger.info("Data Iterator is empty; skipping write to target.")
            return 0
        data = chain((first_record,), data)

        chunk_size = chunk_size if chunk_size else self.settings.DEFAULT_CHUNK_SIZE
        is_bytes = isinstance(first_record, bytes)
        writer = self._write_bytes if is_bytes else self._write_dicts
        return writer(data, target, chunk_size, ignore_errors, operation_type)

    # @abstractmethod (uncomment once all backends use the pattern)
    def _write_bytes(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[bytes],
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""

    # @abstractmethod (uncomment once all backends use the pattern)
    def _write_dicts(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[dict],
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""

    @abstractmethod
    def close(self) -> None:
        """Close the data backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """


def async_enforce_query_checks(method):
    """Enforce query argument type checking for methods using it."""

    @functools.wraps(method)
    async def wrapper(*args, **kwargs):
        """Wrap method execution."""
        query = kwargs.pop("query", None)
        self_ = args[0]
        async for result in method(*args, query=self_.validate_query(query), **kwargs):
            yield result

    return wrapper


class BaseAsyncDataBackend(BaseBackend):
    """Base async data backend interface."""

    type = "data"
    name = "base"
    query_model = BaseQuery
    default_operation_type = BaseOperationType.INDEX
    settings_class = BaseDataBackendSettings

    def validate_query(
        self, query: Union[str, dict, BaseQuery, None] = None
    ) -> BaseQuery:
        """Validate and transform the query."""
        if query is None:
            query = self.query_model()

        if isinstance(query, str):
            query = self.query_model(query_string=query)

        if isinstance(query, dict):
            try:
                query = self.query_model(**query)
            except ValidationError as error:
                msg = "The 'query' argument is expected to be a %s instance. %s"
                errors = error.errors()
                logger.error(msg, self.query_model.__name__, errors)
                raise BackendParameterException(
                    msg % (self.query_model.__name__, errors)
                ) from error

        if not isinstance(query, self.query_model):
            msg = "The 'query' argument is expected to be a %s instance."
            logger.error(msg, self.query_model.__name__)
            raise BackendParameterException(msg % (self.query_model.__name__,))

        logger.debug("Query: %s", str(query))

        return query

    @abstractmethod
    async def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """

    @abstractmethod
    async def list(
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
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

    @abstractmethod
    @async_enforce_query_checks
    async def read(
        self,
        *,
        query: Union[str, BaseQuery] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read records matching the `query` in the `target` container and yield them.

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

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """

    @abstractmethod
    async def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
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

    @abstractmethod
    async def close(self) -> None:
        """Close the data backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
