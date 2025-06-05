"""Tests for Ralph's backend utilities."""

import logging
import sys

if sys.version_info < (3, 10):
    from importlib_metadata import EntryPoint, EntryPoints, entry_points
else:
    from importlib.metadata import EntryPoint, EntryPoints, entry_points

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

from tests.backends.test_utils_backends.valid_backends import TestBackend


def test_backends_loader_get_backends(caplog):
    """Test the `get_backends` function."""

    # Given a non existing backend, the `get_backends` function should skip it.
    with caplog.at_level(logging.DEBUG):
        assert not get_backends(
            EntryPoints(
                [EntryPoint(name="foo", value="non_existent_package:Foo", group="g")]
            ),
            (BaseDataBackend,),
        )

    assert (
        "ralph.backends.loader",
        logging.DEBUG,
        "Failed to import 'foo' backend from 'non_existent_package:Foo': "
        "No module named 'non_existent_package'",
    ) in caplog.record_tuples

    # Given a module with a sub-module raising an exception during the import,
    # the `get_backends` function should skip it.
    entries = EntryPoints(
        [
            EntryPoint(
                name="invalid",
                value=(
                    "tests.backends.test_utils_backends.invalid_backends:InvalidBackend"
                ),
                group="g",
            ),
            EntryPoint(
                name="async_ws_data_backend",
                value=(
                    "tests.backends.test_utils_backends.valid_backends"
                    ":AsyncWSDataBackend"
                ),
                group="g",
            ),
            EntryPoint(
                name="fs_backend",
                value="tests.backends.test_utils_backends.valid_backends:FSDataBackend",
                group="g",
            ),
        ]
    )
    with caplog.at_level(logging.DEBUG):
        assert get_backends(entries, (BaseDataBackend,)) == {
            "fs_backend": FSDataBackend
        }

    assert (
        "ralph.backends.loader",
        logging.DEBUG,
        "Failed to import 'invalid' backend from "
        "'tests.backends.test_utils_backends.invalid_backends:InvalidBackend': "
        "No module named 'invalid_backends'",
    ) in caplog.record_tuples


def test_backends_loader_get_cli_backends(monkeypatch):
    """Test the `get_cli_backends` function."""

    def mock_entry_points(group):
        assert group == "ralph.backends.data"
        return list(entry_points(group="ralph.backends.data")) + [
            EntryPoint(
                name="test_backend",
                value="tests.backends.test_utils_backends.valid_backends:TestBackend",
                group="ralph.backends.data",
            ),
            EntryPoint(
                name="invalid_entry_point_exception",
                value=(
                    "tests.backends.test_utils_backends.invalid_backends:InvalidBackend"
                ),
                group="ralph.backends.data",
            ),
        ]

    monkeypatch.setattr("ralph.backends.loader.entry_points", mock_entry_points)
    get_cli_backends.cache_clear()
    assert get_cli_backends() == {
        "test_backend": TestBackend,
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
    get_cli_backends.cache_clear()
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
    get_cli_backends.cache_clear()
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


def test_backends_loader_get_lrs_backends(monkeypatch):
    """Test the `get_lrs_backends` function."""

    def mock_entry_points(group):
        assert group == "ralph.backends.lrs"
        return list(entry_points(group="ralph.backends.lrs")) + [
            EntryPoint(
                name="test_backend",
                value="tests.backends.test_utils_backends.valid_backends:TestBackend",
                group="ralph.backends.lrs",
            ),
            EntryPoint(
                name="invalid_entry_point_exception",
                value=(
                    "tests.backends.test_utils_backends.invalid_backends:InvalidBackend"
                ),
                group="ralph.backends.lrs",
            ),
        ]

    monkeypatch.setattr("ralph.backends.loader.entry_points", mock_entry_points)
    get_lrs_backends.cache_clear()
    assert get_lrs_backends() == {
        "test_backend": TestBackend,
        "async_es": AsyncESLRSBackend,
        "async_mongo": AsyncMongoLRSBackend,
        "clickhouse": ClickHouseLRSBackend,
        "es": ESLRSBackend,
        "fs": FSLRSBackend,
        "mongo": MongoLRSBackend,
    }
    get_lrs_backends.cache_clear()
