"""Utilities for Ralph."""

import datetime
import logging
import operator
from functools import reduce
from importlib import import_module
from typing import List

from pydantic import BaseModel


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
