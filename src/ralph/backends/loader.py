"""Ralph backend loader."""

import logging
import pkgutil
from functools import lru_cache
from importlib import import_module
from importlib.util import find_spec
from inspect import getmembers, isabstract, isclass
from typing import Dict, Tuple, Type

from ralph.backends.data.base import (
    AsyncListable,
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseDataBackend,
    Listable,
    Writable,
)
from ralph.backends.http.base import BaseHTTPBackend
from ralph.backends.lrs.base import BaseAsyncLRSBackend, BaseLRSBackend
from ralph.backends.stream.base import BaseStreamBackend

logger = logging.getLogger(__name__)


@lru_cache()
def get_backends(packages: Tuple[str], base_backends: Tuple[Type]) -> Dict[str, Type]:
    """Return sub-classes of `base_backends` found in sub-modules of `packages`.

    Args:
        packages (tuple of str): A tuple of dotted package names.
            Ex.: ("ralph.backends.data", "ralph.backends.lrs").
        base_backends (tuple of type): A tuple of base backend classes to search for.
            Ex.: ("BaseDataBackend",)

    Return:
        dict: A dictionary of found non-abstract backend classes by their name property.
            Ex.: {"fs": FSDataBackend}
    """
    module_specs = []
    for package in packages:
        try:
            module_spec = find_spec(package)
        except ModuleNotFoundError:
            module_spec = None

        if not module_spec:
            logger.warning("Could not find '%s' package; skipping it", package)
            continue

        module_specs.append(module_spec)

    modules = []
    for module_spec in module_specs:
        paths = module_spec.submodule_search_locations
        for module_info in pkgutil.iter_modules(paths, prefix=f"{module_spec.name}."):
            modules.append(module_info.name)

    backend_classes = set()
    for module in modules:
        try:
            backend_module = import_module(module)
        except Exception as error:  # noqa: BLE001
            logger.debug("Failed to import %s module: %s", module, error)
            continue
        for _, class_ in getmembers(backend_module, isclass):
            if issubclass(class_, base_backends) and not isabstract(class_):
                backend_classes.add(class_)

    return {
        backend.name: backend
        for backend in sorted(backend_classes, key=lambda x: x.name, reverse=True)
    }


@lru_cache(maxsize=1)
def get_cli_backends() -> Dict[str, Type]:
    """Return Ralph's backend classes for cli usage."""
    dotted_paths = (
        "ralph.backends.data",
        "ralph.backends.http",
        "ralph.backends.stream",
    )
    base_backends = (
        BaseAsyncDataBackend,
        BaseDataBackend,
        BaseHTTPBackend,
        BaseStreamBackend,
    )
    return get_backends(dotted_paths, base_backends)


@lru_cache(maxsize=1)
def get_cli_write_backends() -> Dict[str, Type]:
    """Return Ralph's backends classes for cli write usage."""
    backends = get_cli_backends()
    return {
        name: backend
        for name, backend in backends.items()
        if issubclass(backend, (Writable, AsyncWritable, BaseHTTPBackend))
    }


@lru_cache(maxsize=1)
def get_cli_list_backends() -> Dict[str, Type]:
    """Return Ralph's backends classes for cli list usage."""
    backends = get_cli_backends()
    return {
        name: backend
        for name, backend in backends.items()
        if issubclass(backend, (Listable, AsyncListable))
    }


@lru_cache(maxsize=1)
def get_lrs_backends() -> Dict[str, Type]:
    """Return Ralph's backend classes for LRS usage."""
    return get_backends(
        ("ralph.backends.lrs",),
        (
            BaseAsyncLRSBackend,
            BaseLRSBackend,
        ),
    )
