"""Tests for the base data backend"""

import asyncio
import logging
from typing import Any, Union

import pytest

from ralph.backends.data.base import (
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    Writable,
    get_backend_generic_argument,
)
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import gather_with_limited_concurrency


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
@pytest.mark.parametrize(
    "prefetch,expected_consumed_items",
    [
        # Given `prefetch` set to `None`, 0 or 1, the `read` method should consume data
        # on demand.
        (None, 1),  # One item read -> one item consumed.
        (0, 1),
        (1, 1),
        # Given `prefetch>1`, the `read` method should consume `prefetch` number of
        # items ahead.
        (2, 3),  # One item read -> one item consumed + 2 items prefetched.
        (3, 4),
    ],
)
async def test_backends_data_base_async_read_with_prefetch(
    prefetch, expected_consumed_items
):
    """Test the `BaseAsyncDataBackend.read` method with `prefetch` argument."""
    consumed_items = {"count": 0}

    class MockDataBackend(BaseAsyncDataBackend[BaseDataBackendSettings, BaseQuery]):
        """A class mocking the base database class."""

        async def _read_dicts(self, *args):
            """Yield 6 chunks of `chunk_size` size."""
            for _ in range(6):
                consumed_items["count"] += 1
                yield {"foo": "bar"}

        async def _read_bytes(self, *args):
            pass

        async def status(self):
            pass

        async def close(self):
            pass

    backend = MockDataBackend()
    reader = backend.read(prefetch=prefetch)
    assert await reader.__anext__() == {"foo": "bar"}
    await asyncio.sleep(0.2)
    assert consumed_items["count"] == expected_consumed_items
    assert [_ async for _ in reader] == [
        {"foo": "bar"},
        {"foo": "bar"},
        {"foo": "bar"},
        {"foo": "bar"},
        {"foo": "bar"},
    ]


@pytest.mark.anyio
async def test_backends_data_base_async_read_with_invalid_prefetch(caplog):
    """Test the `BaseAsyncDataBackend.read` method given a `prefetch` argument
    that is less than `0`, should raise a `BackendParameterException`.
    """

    class MockDataBackend(BaseAsyncDataBackend[BaseDataBackendSettings, BaseQuery]):
        """A class mocking the base database class."""

        async def _read_dicts(self, *args):
            pass

        async def _read_bytes(self, *args):
            pass

        async def status(self):
            pass

        async def close(self):
            pass

    msg = "prefetch must be a strictly positive integer"
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            _ = [_ async for _ in MockDataBackend().read(prefetch=-1)]

    assert ("tests.backends.data.test_base", logging.ERROR, msg) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_base_async_read_with_an_error_while_prefetching(caplog):
    """Test the `BaseAsyncDataBackend.read` method given a `prefech` argument and an
    exception while prefetching records, should yield the remaining records before the
    exception and once the last record is yielded, should re-raise the exception.
    """
    consumed_items = {"count": 0}

    class MockDataBackend(BaseAsyncDataBackend[BaseDataBackendSettings, BaseQuery]):
        """A class mocking the base database class."""

        async def _read_dicts(self, *args):
            for _ in range(3):
                consumed_items["count"] += 1
                yield {"foo": "bar"}

            self.logger.error("connection error")
            raise BackendException("connection error")

        async def _read_bytes(self, *args):
            pass

        async def status(self):
            pass

        async def close(self):
            pass

    backend = MockDataBackend()
    reader = backend.read(prefetch=10)
    assert await reader.__anext__() == {"foo": "bar"}
    await asyncio.sleep(0.2)
    # Backend prefetched all records and catched the exception.
    assert consumed_items["count"] == 3
    # Reading the remaining records.
    assert await reader.__anext__() == {"foo": "bar"}
    assert await reader.__anext__() == {"foo": "bar"}
    msg = "connection error"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            await reader.__anext__()

    assert ("tests.backends.data.test_base", logging.ERROR, msg) in caplog.record_tuples


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

        async def status(self):
            pass

        async def close(self):
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


@pytest.mark.anyio
@pytest.mark.parametrize(
    "chunk_size,concurrency,expected_item_count,expected_write_calls",
    [
        # Given a chunk size equal to the size of the data, only one write call should
        # be performed, regardless of how many concurrent requests are allowed.
        (4, None, {4}, 1),
        (4, 1, {4}, 1),
        (4, 20, {4}, 1),
        # Given a chunk size equal to half (or a bit more) of the data, two write
        # calls should be performed.
        (2, 2, {2}, 2),
        (2, 20, {2}, 2),
        (3, 2, {1, 3}, 2),
        (3, 20, {1, 3}, 2),
        # However, given a limit of one concurrent request, only one write call is
        # allowed.
        (2, 1, {4}, 1),
        (3, 1, {4}, 1),
        # Given a chunk size equal to one, up to four concurrent write calls can be
        # performed.
        (1, 1, {4}, 1),
        (1, 2, {1}, 4),
        (1, 20, {1}, 4),
    ],
)
async def test_backends_data_base_async_write_with_concurrency(
    chunk_size, concurrency, expected_item_count, expected_write_calls, monkeypatch
):
    """Test the async `AsyncWritable.write` method with `concurrency` argument."""

    write_calls = {"count": 0}
    gather_calls = {"count": 0}
    data = (i for i in range(4))
    expected_data = {0, 1, 2, 3}
    expected_concurrency = concurrency if concurrency else 1

    class MockAsyncBaseDataBackend(
        BaseAsyncDataBackend[BaseDataBackendSettings, BaseQuery], AsyncWritable
    ):
        """A class mocking the base database class."""

        async def _read_dicts(self, *args):
            pass

        async def _read_bytes(self, *args):
            pass

        async def _write_bytes(self, data, *args):
            pass

        async def _write_dicts(self, data, *args):
            write_calls["count"] += 1
            item_count = 0
            for item in data:
                expected_data.remove(item)
                item_count += 1

            assert item_count in expected_item_count
            return item_count

        async def status(self):
            pass

        async def close(self):
            pass

    async def mock_gather_with_limited_concurrency(num_tasks, *tasks):
        """Mock the gather_with_limited_concurrency method."""
        assert len(tasks) <= expected_concurrency
        assert num_tasks == expected_concurrency
        gather_calls["count"] += 1
        return await gather_with_limited_concurrency(num_tasks, *tasks)

    backend = MockAsyncBaseDataBackend()
    monkeypatch.setattr(
        "ralph.backends.data.base.gather_with_limited_concurrency",
        mock_gather_with_limited_concurrency,
    )

    assert (
        await backend.write(data, chunk_size=chunk_size, concurrency=concurrency) == 4
    )
    # All data should be consumed.
    assert not expected_data
    assert write_calls["count"] == expected_write_calls

    if expected_concurrency == 1:
        assert not gather_calls["count"]
    else:
        assert gather_calls["count"] == max(
            1, int(4 / chunk_size / expected_concurrency)
        )


@pytest.mark.anyio
async def test_backends_data_base_write_with_invalid_parameters(caplog):
    """Test the Writable backend `write` method, given invalid parameters."""

    class MockBaseDataBackend(
        BaseDataBackend[BaseDataBackendSettings, BaseQuery], Writable
    ):
        """A class mocking the base database class."""

        unsupported_operation_types = {BaseOperationType.DELETE}

        def _read_dicts(self, *args):
            pass

        def _read_bytes(self, *args):
            pass

        def _write_bytes(self, *args):
            pass

        def _write_dicts(self, *args):
            return 1

        def status(self):
            pass

        def close(self):
            pass

    backend = MockBaseDataBackend()
    # Given an unsupported `operation_type`, the write method should raise a
    # `BackendParameterException` and log an error.
    msg = "Delete operation_type is not allowed"
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            assert backend.write([{}], operation_type=BaseOperationType.DELETE)

    assert (
        "tests.backends.data.test_base",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples

    # Given an empty data iterator, the write method should log an info and return 0.
    msg = "Data Iterator is empty; skipping write to target"
    with caplog.at_level(logging.INFO):
        assert backend.write([]) == 0

    assert (
        "tests.backends.data.test_base",
        logging.INFO,
        msg,
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_data_base_async_write_with_invalid_parameters(caplog):
    """Test the AsyncWritable backend `write` method, given invalid parameters."""

    class MockAsyncBaseDataBackend(
        BaseAsyncDataBackend[BaseDataBackendSettings, BaseQuery], AsyncWritable
    ):
        """A class mocking the base database class."""

        unsupported_operation_types = {BaseOperationType.DELETE}

        async def _read_dicts(self, *args):
            pass

        async def _read_bytes(self, *args):
            pass

        async def _write_bytes(self, *args):
            pass

        async def _write_dicts(self, *args):
            return 1

        async def status(self):
            pass

        async def close(self):
            pass

    backend = MockAsyncBaseDataBackend()

    # Given `concurrency` is set to a negative value, the write method should raise a
    # `BackendParameterException` and produce an error log.
    msg = "concurrency must be a strictly positive integer"
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            assert await backend.write([{}], concurrency=-1)

    assert (
        "tests.backends.data.test_base",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples

    # Given an unsupported `operation_type`, the write method should raise a
    # `BackendParameterException` and log an error.
    msg = "Delete operation_type is not allowed"
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            assert await backend.write([{}], operation_type=BaseOperationType.DELETE)

    assert (
        "tests.backends.data.test_base",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples

    # Given an empty data iterator, the write method should log an info and return 0.
    msg = "Data Iterator is empty; skipping write to target"
    with caplog.at_level(logging.INFO):
        assert await backend.write([]) == 0

    assert (
        "tests.backends.data.test_base",
        logging.INFO,
        msg,
    ) in caplog.record_tuples
