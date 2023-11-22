"""Utilities for Ralph."""

import asyncio
import datetime
import json
import logging
import operator
from functools import reduce
from importlib import import_module
from inspect import getmembers, isclass, iscoroutine
from itertools import islice
from logging import Logger, getLogger
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from ralph.exceptions import BackendException, UnsupportedBackendException

logger = logging.getLogger(__name__)


def import_subclass(dotted_path: str, parent_class: Any) -> Any:
    """Import a dotted module path.

    Return the class that is a subclass of `parent_class` inside this module.
    Raise ImportError if the import failed.
    """
    module = import_module(dotted_path)

    for _, class_ in getmembers(module, isclass):
        if issubclass(class_, parent_class):
            return class_

    raise ImportError(
        f'Module "{dotted_path}" does not define a subclass of "{parent_class}" class'
    )


# Taken from Django utilities
# https://docs.djangoproject.com/en/3.1/_modules/django/utils/module_loading/#import_string
def import_string(dotted_path: str) -> Any:
    """Import a dotted module path.

    Return the attribute/class designated by the last name in the path.
    Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            f'Module "{module_path}" does not define a "{class_name}" attribute/class'
        ) from err


def get_backend_class(backends: Dict[str, Type], name: str) -> Any:
    """Return the backend class from available backends by its name."""
    backend_class = backends.get(name)
    if not backend_class:
        msg = "'%s' backend not found in available backends: %s"
        available_backends = ", ".join(backends.keys())
        logger.error(msg, name, available_backends)
        raise UnsupportedBackendException(msg % (name, available_backends))
    return backend_class


def get_backend_instance(backend_class: Type, options: Dict) -> Any:
    """Return the instantiated backend given the backend class and options."""
    prefix = f"{backend_class.name}_"
    # Filter backend-related parameters. Parameter name is supposed to start
    # with the backend name
    options = {
        name.replace(prefix, "").upper(): value
        for name, value in options.items()
        if name.startswith(prefix) and value is not None
    }
    return backend_class(backend_class.settings_class(**options))


def get_root_logger() -> Logger:
    """Get main Ralph logger."""
    ralph_logger = getLogger("ralph")
    ralph_logger.propagate = True

    return ralph_logger


def now() -> str:
    """Return the current UTC time in ISO format."""
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()


def get_dict_value_from_path(dict_: Dict, path: Sequence[str]) -> Union[Dict, None]:
    """Get a nested dictionary value.

    Args:
        dict_ (dict): dictionary of values to which the reduction is
            applied
        path (List): array of keys representing the path to the value
    """
    if path is None:
        return None
    try:
        return reduce(operator.getitem, path, dict_)
    except (KeyError, TypeError):
        return None


def set_dict_value_from_path(dict_: Dict, path: List[str], value: Any) -> None:
    """Set a nested dictionary value.

    Args:
        dict_ (dict): dictionary where the given value is set
        path (List): array of keys representing the path to the value
        value: value to be set
    """
    for key in path[:-1]:
        dict_ = dict_.setdefault(key, {})
    dict_[path[-1]] = value


async def gather_with_limited_concurrency(num_tasks: Optional[int], *tasks: Any) -> Any:
    """Gather no more than `num_tasks` tasks at time.

    Args:
        num_tasks: the maximum number of tasks to run concurrently, if None,
            no maximum value is set
        tasks: tasks to run concurrently
    """
    if num_tasks is not None:
        semaphore = asyncio.Semaphore(num_tasks)

        async def sem_task(task: Any) -> Any:
            async with semaphore:
                return await task

        group = asyncio.gather(*(sem_task(task) for task in tasks))
    else:
        group = asyncio.gather(*tasks)

    # Cancel background tasks on first error
    try:
        return await group
    except Exception as exception:
        group.cancel()
        raise exception


def statements_are_equivalent(statement_1: dict, statement_2: dict) -> bool:
    """Check if statements are equivalent.

    To be equivalent, they must be identical on all fields not modified on input by the
    LRS and identical on other fields, if these fields are present in both
    statements. For example, if an "authority" field is present in only one statement,
    they may still be equivalent.
    """
    # Check that unmutable fields have the same values
    fields = {"actor", "verb", "object", "id", "result", "context", "attachments"}

    # Check that some fields enriched by the LRS are equal when in both statements
    # The LRS specification excludes the fields below from equivalency. It was
    # decided to include them anyway as their value is inherent to the statements.
    other_fields = {"timestamp", "version"}  # "authority" and "stored" remain ignored.
    fields.update(other_fields & statement_1.keys() & statement_2.keys())

    if any(statement_1.get(field) != statement_2.get(field) for field in fields):
        return False
    return True


T = TypeVar("T")


def parse_iterable_to_dict(
    raw_documents: Iterable[T],
    ignore_errors: bool,
    logger_class: logging.Logger,
    parser: Callable[[T], Dict[str, Any]] = json.loads,
    exceptions: Tuple[Type[Exception], ...] = (TypeError, json.JSONDecodeError),
) -> Iterator[dict]:
    """Read the `raw_documents` Iterable and yield dictionaries."""
    for i, raw_document in enumerate(raw_documents):
        try:
            yield parser(raw_document)
        except exceptions as error:
            msg = "Failed to decode JSON: %s, for document: %s, at line %s"
            if ignore_errors:
                logger_class.warning(msg, error, raw_document, i)
                continue
            logger_class.error(msg, error, raw_document, i)
            raise BackendException(msg % (error, raw_document, i)) from error


async def async_parse_iterable_to_dict(
    raw_documents: AsyncIterable[T],
    ignore_errors: bool,
    logger_class: logging.Logger,
    parser: Callable[[T], Dict[str, Any]] = json.loads,
    exceptions: Tuple[Type[Exception], ...] = (TypeError, json.JSONDecodeError),
) -> AsyncIterator[dict]:
    """Read the `raw_documents` Iterable and yield dictionaries."""
    i = 0
    async for raw_document in raw_documents:
        try:
            yield parser(raw_document)
        except exceptions as error:
            msg = "Failed to decode JSON: %s, for document: %s, at line %s"
            if ignore_errors:
                logger_class.warning(msg, error, raw_document, i)
                continue
            logger_class.error(msg, error, raw_document, i)
            raise BackendException(msg % (error, raw_document, i)) from error

        i += 1


def parse_dict_to_bytes(
    documents: Iterable[Dict[str, Any]],
    encoding: str,
    ignore_errors: bool,
    logger_class: logging.Logger,
) -> Iterator[bytes]:
    """Read the `documents` Iterable with the `encoding` and yield bytes."""
    for i, document in enumerate(documents):
        try:
            yield f"{json.dumps(document)}\n".encode(encoding)
        except (TypeError, ValueError) as error:
            msg = "Failed to encode JSON: %s, for document: %s, at line %s"
            if ignore_errors:
                logger_class.warning(msg, error, document, i)
                continue
            logger_class.error(msg, error, document, i)
            raise BackendException(msg % (error, document, i)) from error


async def async_parse_dict_to_bytes(
    documents: AsyncIterable[Dict[str, Any]],
    encoding: str,
    ignore_errors: bool,
    logger_class: logging.Logger,
) -> AsyncIterator[bytes]:
    """Read the `documents` Iterable with the `encoding` and yield bytes."""
    i = 0
    async for document in documents:
        try:
            yield f"{json.dumps(document)}\n".encode(encoding)
        except (TypeError, ValueError) as error:
            msg = "Failed to encode JSON: %s, for document: %s, at line %s"
            if ignore_errors:
                logger_class.warning(msg, error, document, i)
                continue
            logger_class.error(msg, error, document, i)
            raise BackendException(msg % (error, document, i)) from error

        i += 1


def iter_by_batch(iterable: Iterable, n: int) -> Iterable[list]:
    """Batch `iterable` into lists of length `n`. The last batch may be less than `n`.

    Inspired by itertools.batched introduced in python 3.12
    """
    if n < 1:
        raise ValueError("n must be at least one")

    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch


def iter_over_async(agenerator) -> Iterable:
    """Iterate synchronously over an asynchronous generator."""
    loop = asyncio.get_event_loop()
    aiterator = agenerator.__aiter__()

    async def get_next():
        """Get the next element from the async iterator."""
        try:
            obj = await aiterator.__anext__()
            return False, obj
        except StopAsyncIteration:
            return True, None

    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        yield obj


def execute_async(method):
    """Run asynchronous method in a synchronous context."""

    def wrapper(*args, **kwargs):
        """Wrap method execution."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(method(*args, **kwargs))

    return wrapper


async def await_if_coroutine(value):
    """Await the value if it is a coroutine, else return synchronously."""
    if iscoroutine(value):
        return await value
    return value
