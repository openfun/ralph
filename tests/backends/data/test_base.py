"""Tests for the base data backend"""
import logging

import pytest

from ralph.backends.data.base import BaseDataBackend, BaseQuery, enforce_query_checks
from ralph.exceptions import BackendParameterException


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, BaseQuery()),
        ("foo", BaseQuery(query_string="foo")),
        (BaseQuery(query_string="foo"), BaseQuery(query_string="foo")),
    ],
)
def test_backends_data_base_enforce_query_checks_with_valid_input(value, expected):
    """Test the enforce_query_checks function given valid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base data backend class."""

        def __init__(self, settings=None):
            """Instantiate the Mock data backend."""

        @enforce_query_checks
        def read(self, query=None):
            """Mock the base database read method."""

            assert query == expected

        def status(self):
            pass

        def close(self):
            pass

    MockBaseDataBackend().read(query=value)


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

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base database class."""

        def __init__(self, settings=None):
            """Instantiate the Mock data backend."""

        @enforce_query_checks
        def read(self, query=None):
            """Mock the base database read method."""

            return None

        def status(self):
            pass

        def close(self):
            pass

    with pytest.raises(BackendParameterException, match=error):
        with caplog.at_level(logging.ERROR):
            MockBaseDataBackend().read(query=value)

    error = error.replace("\\", "")
    assert ("ralph.backends.data.base", logging.ERROR, error) in caplog.record_tuples
