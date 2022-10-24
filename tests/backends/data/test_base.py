"""Tests for the base data backend"""

import pytest
from pydantic import BaseModel

from ralph.backends.data.base import BaseDataBackend, enforce_query_checks
from ralph.exceptions import BackendParameterException


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, BaseModel()),
        ("foo", BaseModel(query_string="foo")),
        (BaseModel(foo="foo"), BaseModel(foo="foo")),
    ],
)
def test_backends_data_base_enforce_query_checks_with_valid_input(value, expected):
    """Test the enforce_query_checks function given valid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base database class."""

        query_model = BaseModel

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


@pytest.mark.parametrize("value", [[], {}])
def test_backends_data_base_enforce_query_checks_with_invalid_input(value):
    """Test the enforce_query_checks function given invalid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base database class."""

        query_model = BaseModel

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

    error = "The 'query' argument is expected to be a BaseModel instance."
    with pytest.raises(BackendParameterException, match=error):
        MockBaseDataBackend().read(query=value)
