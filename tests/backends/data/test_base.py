"""Tests for the base data backend"""

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
    """Tests the enforce_query_checks function given valid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base database class."""

        def __init__(self, settings=None):
            """Instantiates the Mock data backend."""

        @enforce_query_checks
        def read(self, query=None):  # pylint: disable=no-self-use,arguments-differ
            """Mock the base database read method."""

            assert query == expected

        def status(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def list(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def write(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

    MockBaseDataBackend().read(query=value)


@pytest.mark.parametrize("value", [[], {"foo": "bar"}])
def test_backends_data_base_enforce_query_checks_with_invalid_input(value):
    """Tests the enforce_query_checks function given invalid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base database class."""

        def __init__(self, settings=None):
            """Instantiates the Mock data backend."""

        @enforce_query_checks
        def read(self, query=None):  # pylint: disable=no-self-use,arguments-differ
            """Mock the base database read method."""

            return None

        def status(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def list(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

        def write(self):  # pylint: disable=arguments-differ,missing-function-docstring
            pass

    error = "The 'query' argument is expected to be a BaseQuery instance."
    with pytest.raises(BackendParameterException, match=error):
        MockBaseDataBackend().read(query=value)
