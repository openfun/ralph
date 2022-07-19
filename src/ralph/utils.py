"""Utilities for Ralph"""

import datetime
import logging
import operator
from functools import reduce
from importlib import import_module


# Taken from Django utilities
# https://docs.djangoproject.com/en/3.1/_modules/django/utils/module_loading/#import_string
def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
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


def get_class_names(modules):
    """Get class name attributes from class modules list"""

    return [import_string(module).name for module in modules]


def get_class_from_name(name, modules):
    """Get class given its name in a modules list"""

    for module in modules:
        klass = import_string(module)
        if klass.name == name:
            return klass
    raise ImportError(f"{name} class is not available")


def get_instance_from_class(klass, **init_parameters):
    """Return a class instance given class-name-prefixed init parameters"""

    # Filter backend-related parameters. Parameter name is supposed to start
    # with the backend name
    names = filter(lambda p: p.startswith(klass.name), init_parameters.keys())
    parameters = {
        name.replace(f"{klass.name}_", ""): init_parameters[name] for name in names
    }

    return klass(**parameters)


def get_root_logger():
    """Get main Ralph logger"""

    ralph_logger = logging.getLogger("ralph")
    ralph_logger.propagate = True

    return ralph_logger


def now():
    """Return the current UTC time in ISO format"""

    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()


def get_dict_value_from_path(dict_: dict, path: list[str]):
    """Gets a nested dictionary value using an array of keys representing the path
    to the value.
    """

    if path is None:
        return None
    try:
        return reduce(operator.getitem, path, dict_)
    except (KeyError, TypeError):
        return None


def set_dict_value_from_path(dict_: dict, path: list[str], value: any):
    """Sets a nested dictionary value using an array of keys representing the path
    to the value.
    """

    for key in path[:-1]:
        dict_ = dict_.setdefault(key, {})
    dict_[path[-1]] = value
