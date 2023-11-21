"""Tests for Ralph's backend utilities."""

import logging

from ralph.backends.data.async_es import AsyncESDataBackend
from ralph.backends.data.async_lrs import AsyncLRSDataBackend
from ralph.backends.data.async_mongo import AsyncMongoDataBackend
from ralph.backends.data.async_ws import AsyncWSDataBackend
from ralph.backends.data.base import BaseDataBackend
from ralph.backends.data.clickhouse import ClickHouseDataBackend
from ralph.backends.data.es import ESDataBackend
from ralph.backends.data.fs import FSDataBackend
from ralph.backends.data.ldp import LDPDataBackend
from ralph.backends.data.lrs import LRSDataBackend
from ralph.backends.data.mongo import MongoDataBackend
from ralph.backends.data.s3 import S3DataBackend
from ralph.backends.data.swift import SwiftDataBackend
from ralph.backends.loader import (
    get_backends,
    get_cli_backends,
    get_cli_list_backends,
    get_cli_write_backends,
    get_lrs_backends,
)
from ralph.backends.lrs.async_es import AsyncESLRSBackend
from ralph.backends.lrs.async_mongo import AsyncMongoLRSBackend
from ralph.backends.lrs.clickhouse import ClickHouseLRSBackend
from ralph.backends.lrs.es import ESLRSBackend
from ralph.backends.lrs.fs import FSLRSBackend
from ralph.backends.lrs.mongo import MongoLRSBackend


def test_backends_loader_get_backends(caplog):
    """Test the `get_backends` function."""

    # Given a non existing module name, the `get_backends` function should skip it.
    with caplog.at_level(logging.WARNING):
        assert not get_backends(("non_existent_package.foo",), (BaseDataBackend,))

    assert (
        "ralph.backends.loader",
        logging.WARNING,
        "Could not find 'non_existent_package.foo' package; skipping it",
    ) in caplog.record_tuples

    # Given a module with a sub-module raising an exception during the import,
    # the `get_backends` function should skip it.
    paths = ("tests.backends.test_utils_backends",)
    with caplog.at_level(logging.DEBUG):
        assert get_backends(paths, (BaseDataBackend,)) == {"fs": FSDataBackend}

    assert (
        "ralph.backends.loader",
        logging.DEBUG,
        "Failed to import tests.backends.test_utils_backends.invalid_backends module: "
        "No module named 'invalid_backends'",
    ) in caplog.record_tuples


def test_backends_loader_get_cli_backends():
    """Test the `get_cli_backends` function."""
    assert get_cli_backends() == {
        "async_es": AsyncESDataBackend,
        "async_lrs": AsyncLRSDataBackend,
        "async_mongo": AsyncMongoDataBackend,
        "async_ws": AsyncWSDataBackend,
        "clickhouse": ClickHouseDataBackend,
        "es": ESDataBackend,
        "fs": FSDataBackend,
        "ldp": LDPDataBackend,
        "lrs": LRSDataBackend,
        "mongo": MongoDataBackend,
        "s3": S3DataBackend,
        "swift": SwiftDataBackend,
    }


def test_backends_loader_get_cli_write_backends():
    """Test the `get_cli_write_backends` function."""
    assert get_cli_write_backends() == {
        "async_es": AsyncESDataBackend,
        "async_lrs": AsyncLRSDataBackend,
        "async_mongo": AsyncMongoDataBackend,
        "clickhouse": ClickHouseDataBackend,
        "es": ESDataBackend,
        "fs": FSDataBackend,
        "lrs": LRSDataBackend,
        "mongo": MongoDataBackend,
        "s3": S3DataBackend,
        "swift": SwiftDataBackend,
    }


def test_backends_loader_get_cli_list_backends():
    """Test the `get_cli_list_backends` function."""
    assert get_cli_list_backends() == {
        "async_es": AsyncESDataBackend,
        "async_mongo": AsyncMongoDataBackend,
        "clickhouse": ClickHouseDataBackend,
        "es": ESDataBackend,
        "fs": FSDataBackend,
        "ldp": LDPDataBackend,
        "mongo": MongoDataBackend,
        "s3": S3DataBackend,
        "swift": SwiftDataBackend,
    }


def test_backends_loader_get_lrs_backends():
    """Test the `get_lrs_backends` function."""
    assert get_lrs_backends() == {
        "async_es": AsyncESLRSBackend,
        "async_mongo": AsyncMongoLRSBackend,
        "clickhouse": ClickHouseLRSBackend,
        "es": ESLRSBackend,
        "fs": FSLRSBackend,
        "mongo": MongoLRSBackend,
    }
