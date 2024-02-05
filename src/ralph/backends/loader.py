"""Ralph backend loader."""

import logging
from functools import lru_cache
from typing import Dict, List, Tuple

from ralph.backends.data.base import (
    AsyncListable,
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseDataBackend,
    Listable,
    Writable,
)
from ralph.backends.lrs.base import BaseAsyncLRSBackend, BaseLRSBackend
from ralph.utils import import_string

logger = logging.getLogger(__name__)

DATA_BACKENDS: List[str] = [
    "ralph.backends.data.async_es.AsyncESDataBackend",
    "ralph.backends.data.async_lrs.AsyncLRSDataBackend",
    "ralph.backends.data.async_mongo.AsyncMongoDataBackend",
    "ralph.backends.data.async_ws.AsyncWSDataBackend",
    "ralph.backends.data.clickhouse.ClickHouseDataBackend",
    "ralph.backends.data.es.ESDataBackend",
    "ralph.backends.data.fs.FSDataBackend",
    "ralph.backends.data.ldp.LDPDataBackend",
    "ralph.backends.data.lrs.LRSDataBackend",
    "ralph.backends.data.mongo.MongoDataBackend",
    "ralph.backends.data.s3.S3DataBackend",
    "ralph.backends.data.swift.SwiftDataBackend",
]
LRS_BACKENDS: List[str] = [
    "ralph.backends.lrs.async_es.AsyncESLRSBackend",
    "ralph.backends.lrs.async_mongo.AsyncMongoLRSBackend",
    "ralph.backends.lrs.clickhouse.ClickHouseLRSBackend",
    "ralph.backends.lrs.es.ESLRSBackend",
    "ralph.backends.lrs.fs.FSLRSBackend",
    "ralph.backends.lrs.mongo.MongoLRSBackend",
]


def get_backends(
    backends: List[str], base_backends: Tuple[type, ...]
) -> Dict[str, type]:
    """Return sub-classes of `base_backends` from `backends`.

    Args:
        backends (list of str): A list of dotted backend import paths.
            Ex.: ["foo.bar.BackendA", "foo.bar.BackendB"].
        base_backends (tuple of type): A tuple of base backend classes to filter for.
            Ex.: ("BaseDataBackend",)

    Return:
        dict: A dictionary of backend classes by their name property.
            Ex.: {"fs": FSDataBackend}
    """
    backend_classes = []
    for backend in backends:
        try:
            backend_class = import_string(backend)
        except Exception as error:  # noqa: BLE001
            logger.debug("Failed to import '%s' backend: %s", backend, error)
            continue

        if issubclass(backend_class, base_backends):
            backend_classes.append(backend_class)
    return {
        backend.name: backend
        for backend in sorted(backend_classes, key=lambda x: x.name, reverse=True)
    }


@lru_cache(maxsize=1)
def get_cli_backends() -> Dict[str, type]:
    """Return Ralph's backend classes for cli usage."""
    base_backends = (BaseAsyncDataBackend, BaseDataBackend)
    return get_backends(DATA_BACKENDS, base_backends)


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
    return get_backends(LRS_BACKENDS, (BaseAsyncLRSBackend, BaseLRSBackend))
