"""Tests for the base data backend"""
import logging

import pytest

from ralph.backends.data.base import BaseDataBackend, BaseQuery
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
    """Test the validate_backend_query function given valid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base data backend class."""

        def _read_bytes(self, query, target, chunk_size, ignore_errors):
            """Mock the base database read_bytes method."""
            assert query == expected
            yield

        def _read_dicts(self, query, target, chunk_size, ignore_errors):
            """Mock the base database read_dicts method."""
            assert query == expected
            yield

        def status(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def list(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def _write_bytes(self):
            # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def _write_dicts(self):
            # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def close(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

    list(MockBaseDataBackend().read(query=value))


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
def test_backends_data_base_validate_backend_query_with_invalid_input(
    value, error, caplog
):
    """Test the enforce_query_checks function given invalid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base data backend class."""

        def _read_bytes(self, query, target, chunk_size, ignore_errors):
            """Mock the base database read_bytes method."""
            yield

        def _read_dicts(self, query, target, chunk_size, ignore_errors):
            """Mock the base database read_dicts method."""
            yield

        def status(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def list(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def _write_bytes(self):
            # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def _write_dicts(self):
            # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def close(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

    with pytest.raises(BackendParameterException, match=error):
        with caplog.at_level(logging.ERROR):
            list(MockBaseDataBackend().read(query=value))

    error = error.replace("\\", "")
    assert ("ralph.backends.data.base", logging.ERROR, error) in caplog.record_tuples
