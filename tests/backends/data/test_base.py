"""Tests for the base data backend"""

import logging
from typing import Any, Union

import pytest

from ralph.backends.data.base import (
    BaseAsyncDataBackend,
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseQuery,
    get_backend_generic_argument,
)
from ralph.exceptions import BackendParameterException


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, BaseQuery()),
        ("foo", BaseQuery(query_string="foo")),
        (BaseQuery(query_string="foo"), BaseQuery(query_string="foo")),
    ],
)
def test_backends_data_base_validate_backend_query_with_valid_input(value, expected):
    """Test the enforce_query_checks function given valid input."""

    class MockBaseDataBackend(BaseDataBackend[BaseDataBackendSettings, BaseQuery]):
        """A class mocking the base data backend class."""

        def _read_dicts(self, query, *args):
            yield query == expected

        def _read_bytes(self, query, *args):
            yield query == expected

        def status(self):
            pass

        def close(self):
            pass

    assert list(MockBaseDataBackend().read(query=value, raw_output=True)) == [True]
    assert list(MockBaseDataBackend().read(query=value, raw_output=False)) == [True]


@pytest.mark.parametrize(
    "value,error",
    [
        ([], r"The 'query' argument is expected to be a BaseQuery instance."),
        (
            {"foo": "bar"},
            r"The 'query' argument is expected to be a BaseQuery instance. "
            r"\[\{'loc': \('foo',\), 'msg': 'extra fields not permitted', "
            r"'type': 'value_error.extra'\}\]",
        ),
    ],
)
def test_backends_data_base_enforce_query_checks_with_invalid_input(
    value, error, caplog
):
    """Test the enforce_query_checks function given invalid input."""

    class MockBaseDataBackend(BaseDataBackend[BaseDataBackendSettings, BaseQuery]):
        """A class mocking the base database class."""

        def _read_dicts(self, query, *args):
            yield

        def _read_bytes(self, query, *args):
            yield

        def status(self):
            pass

        def close(self):
            pass

    with pytest.raises(BackendParameterException, match=error):
        with caplog.at_level(logging.ERROR):
            list(MockBaseDataBackend().read(query=value))

    error = error.replace("\\", "")
    module_name = "tests.backends.data.test_base"
    assert (module_name, logging.ERROR, error) in caplog.record_tuples


def test_backends_data_base_get_backend_generic_argument():
    """Test the get_backend_generic_argument function."""

    assert get_backend_generic_argument(BaseDataBackendSettings, 0) is None
    assert get_backend_generic_argument(BaseDataBackend, -2) is None
    assert get_backend_generic_argument(BaseDataBackend, -1) is BaseQuery
    assert get_backend_generic_argument(BaseDataBackend, 0) is BaseDataBackendSettings
    assert get_backend_generic_argument(BaseDataBackend, 1) is BaseQuery
    assert get_backend_generic_argument(BaseDataBackend, 2) is None

    class DummySettings(BaseDataBackendSettings):
        """Dummy Settings."""

    class DummyQuery(BaseQuery):
        """Dummy Query."""

    class DummyBackend(BaseDataBackend[DummySettings, DummyQuery]):
        """Dummy Backend."""

    assert get_backend_generic_argument(DummyBackend, 0) is DummySettings
    assert get_backend_generic_argument(DummyBackend, 1) is DummyQuery

    class DummyAnyBackend(BaseDataBackend[DummySettings, Any]):
        """Dummy Any Backend."""

    assert get_backend_generic_argument(DummyAnyBackend, 0) is DummySettings
    assert get_backend_generic_argument(DummyAnyBackend, 1) is None

    # Given a backend that does not follow type hints, the function should return None.
    class DummyBadBackend(BaseDataBackend[Union[dict, int], Union[int, str]]):
        """Dummy bad backend."""

    assert get_backend_generic_argument(DummyBadBackend, 0) is None
    assert get_backend_generic_argument(DummyBadBackend, 1) is None


def test_backends_data_base_read_with_max_statements():
    """Test the `BaseDataBackend.read` method with `max_statements` argument."""

    class MockBaseDataBackend(BaseDataBackend[BaseDataBackendSettings, BaseQuery]):
        """A class mocking the base database class."""

        def _read_dicts(self, *args):
            yield from ({}, {}, {}, {})

        def _read_bytes(self, *args):
            yield from (b"", b"", b"")

        def status(self):
            pass

        def close(self):
            pass

    backend = MockBaseDataBackend()
    assert list(backend.read()) == [{}, {}, {}, {}]
    assert list(backend.read(raw_output=True)) == [b"", b"", b""]

    assert list(backend.read(max_statements=9)) == [{}, {}, {}, {}]
    assert list(backend.read(max_statements=9, raw_output=True)) == [b"", b"", b""]

    assert list(backend.read(max_statements=3)) == [{}, {}, {}]
    assert list(backend.read(max_statements=3, raw_output=True)) == [b"", b"", b""]

    assert not list(backend.read(max_statements=0))
    assert not list(backend.read(max_statements=0, raw_output=True))


@pytest.mark.anyio
async def test_backends_data_base_async_read_with_max_statements():
    """Test the async `BaseDataBackend.read` method with `max_statements` argument."""

    class MockAsyncBaseDataBackend(
        BaseAsyncDataBackend[BaseDataBackendSettings, BaseQuery]
    ):
        """A class mocking the base database class."""

        async def _read_dicts(self, *args):
            for _ in range(4):
                yield {}

        async def _read_bytes(self, *args):
            for _ in range(3):
                yield b""

        def status(self):
            pass

        def close(self):
            pass

    backend = MockAsyncBaseDataBackend()
    assert [_ async for _ in backend.read()] == [{}, {}, {}, {}]
    assert [_ async for _ in backend.read(raw_output=True)] == [b"", b"", b""]

    assert [_ async for _ in backend.read(max_statements=9)] == [{}, {}, {}, {}]
    assert [_ async for _ in backend.read(max_statements=9, raw_output=True)] == [
        b"",
        b"",
        b"",
    ]

    assert [_ async for _ in backend.read(max_statements=3)] == [{}, {}, {}]
    assert [_ async for _ in backend.read(max_statements=3, raw_output=True)] == [
        b"",
        b"",
        b"",
    ]

    assert not [_ async for _ in backend.read(max_statements=0)]
    assert not [_ async for _ in backend.read(max_statements=0, raw_output=True)]
