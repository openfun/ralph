"""Utilities for Ralph"""

import logging
from importlib import import_module

import click_log


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
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err


def get_class_from_name(name, modules):
    """Get class given its name in a module enum"""

    for module in modules:
        klass = import_string(module.value)
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
    click_log.basic_config(ralph_logger)
    ralph_logger.propagate = True

    return ralph_logger
