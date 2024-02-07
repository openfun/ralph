"""Ralph backend loader."""

import logging
import sys
from functools import lru_cache
from typing import Dict, Tuple

if sys.version_info < (3, 10):
    from importlib_metadata import EntryPoints, entry_points
else:
    from importlib.metadata import EntryPoints, entry_points

from ralph.backends.data.base import (
    AsyncListable,
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseDataBackend,
    Listable,
    Writable,
)
from ralph.backends.lrs.base import BaseAsyncLRSBackend, BaseLRSBackend

logger = logging.getLogger(__name__)


def get_backends(
    backends: EntryPoints, base_backends: Tuple[type, ...]
) -> Dict[str, type]:
    """Return sub-classes of `base_backends` from `backends`.

    Args:
        backends (EntryPoints): EntryPoints pointing to backend classes.
            Ex.: [EntryPoint(name="backend_name", value="foo.bar:BackendA"].
        base_backends (tuple of type): A tuple of base backend classes to filter for.
            Ex.: ("BaseDataBackend",)

    Return:
        dict: A dictionary of backend classes by their `EntryPoint.name` property.
            Ex.: {"fs": FSDataBackend}
    """
    backend_classes = {}
    for backend in sorted(backends, key=lambda x: x.name, reverse=True):
        try:
            backend_class = backend.load()
        except Exception as error:  # noqa: BLE001
            logger.debug(
                "Failed to import '%s' backend from '%s': %s",
                backend.name,
                backend.value,
                error,
            )
            continue

        if issubclass(backend_class, base_backends):
            backend_classes[backend.name] = backend_class

    return backend_classes


@lru_cache(maxsize=1)
def get_cli_backends() -> Dict[str, type]:
    """Return Ralph's backend classes for cli usage."""
    base_backends = (BaseAsyncDataBackend, BaseDataBackend)
    data_backends = entry_points(group="ralph.backends.data")
    return get_backends(data_backends, base_backends)


@lru_cache(maxsize=1)
def get_cli_write_backends() -> Dict[str, type]:
    """Return Ralph's backends classes for cli write usage."""
    return {
        name: backend
        for name, backend in get_cli_backends().items()
        if issubclass(backend, (Writable, AsyncWritable))
    }


@lru_cache(maxsize=1)
def get_cli_list_backends() -> Dict[str, type]:
    """Return Ralph's backends classes for cli list usage."""
    return {
        name: backend
        for name, backend in get_cli_backends().items()
        if issubclass(backend, (Listable, AsyncListable))
    }


@lru_cache(maxsize=1)
def get_lrs_backends() -> Dict[str, type]:
    """Return Ralph's backend classes for LRS usage."""
    lrs_backends = entry_points(group="ralph.backends.lrs")
    return get_backends(lrs_backends, (BaseAsyncLRSBackend, BaseLRSBackend))
