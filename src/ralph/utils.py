"""Utilities for Ralph."""

import asyncio
import datetime
import json
import logging
import operator
from functools import reduce
from importlib import import_module
from typing import Any, Dict, Iterable, Iterator, List, Union

from pydantic import BaseModel

from ralph.exceptions import BackendException


# Taken from Django utilities
# https://docs.djangoproject.com/en/3.1/_modules/django/utils/module_loading/#import_string
def import_string(dotted_path):
    """Import a dotted module path.

    Returns the attribute/class designated by the last name in the path.
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


def get_backend_type(backends: BaseModel, backend_name: str):
    """Returns the backend type from a backend name."""
    backend_name = backend_name.upper()
    for _, backend_type in backends:
        if hasattr(backend_type, backend_name):
            return backend_type
    return None


def get_backend_instance(backend_type: BaseModel, backend_name: str, options: dict):
    """Returns the instantiated backend instance given backend-name-prefixed options."""
    prefix = f"{backend_name}_"
    # Filter backend-related parameters. Parameter name is supposed to start
    # with the backend name
    names = filter(lambda key: key.startswith(prefix), options.keys())
    options = {name.replace(prefix, ""): options[name] for name in names}
    return getattr(backend_type, backend_name.upper()).get_instance(**options)


def get_root_logger():
    """Get main Ralph logger."""
    ralph_logger = logging.getLogger("ralph")
    ralph_logger.propagate = True

    return ralph_logger


def now():
    """Return the current UTC time in ISO format."""
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()


def get_dict_value_from_path(dict_: dict, path: List[str]):
    """Gets a nested dictionary value.

    Args:
        dict_ (dict): dictionnary of values to which the reduction is
            applied
        path (List): array of keys representing the path to the value
    """
    if path is None:
        return None
    try:
        return reduce(operator.getitem, path, dict_)
    except (KeyError, TypeError):
        return None


def set_dict_value_from_path(dict_: dict, path: List[str], value: any):
    """Sets a nested dictionary value.

    Args:
        dict_ (dict): dictionnary where the given value is set
        path (List): array of keys representing the path to the value
        value: value to be set
    """
    for key in path[:-1]:
        dict_ = dict_.setdefault(key, {})
    dict_[path[-1]] = value


async def gather_with_limited_concurrency(num_tasks: Union[None, int], *tasks):
    """Gather no more than `num_tasks` tasks at time.

    Args:
        num_tasks: the maximum number of tasks to run concurrently, if None,
            no maximum value is set
        tasks: tasks to run concurrently
    """
    if num_tasks is not None:
        semaphore = asyncio.Semaphore(num_tasks)

        async def sem_task(task):
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


def statements_are_equivalent(statement_1: dict, statement_2: dict):
    """Check if statements are equivalent.

    To be equivalent, they must be identical on all fields not modified on input by the
    LRS and identical on other fields, if these fields are present in both
    statements. For example, if an "authority" field is present in only one statement,
    they may still be equivalent.
    """
    # Check that unmutable fields have the same values
    fields = ["actor", "verb", "object", "id", "result", "context", "attachements"]

    # Check that some fields enriched by the LRS are equal when in both statements
    # The LRS specification excludes the fields below from equivalency. It was
    # decided to include them anyway as their value is inherent to the statements.
    other_fields = {"timestamp", "version"}  # "authority" and "stored" remain ignored.
    fields.extend(other_fields & statement_1.keys() & statement_2.keys())

    if any(statement_1.get(field) != statement_2.get(field) for field in fields):
        return False
    return True


def parse_bytes_to_dict(
    raw_documents: Iterable[bytes], ignore_errors: bool, logger_class: logging.Logger
) -> Iterator[dict]:
    """Read the `raw_documents` Iterable and yield dictionaries."""
    for raw_document in raw_documents:
        try:
            yield json.loads(raw_document)
        except (TypeError, json.JSONDecodeError) as error:
            msg = "Failed to decode JSON: %s, for document: %s"
            logger_class.error(msg, error, raw_document)
            if ignore_errors:
                continue
            raise BackendException(msg % (error, raw_document)) from error


def read_raw(documents: Iterable[Dict[str, Any]], encoding: str) -> Iterator[bytes]:
    """Read the `documents` Iterable with the `encoding` and yield bytes."""
    for document in documents:
        yield json.dumps(document).encode(encoding)
