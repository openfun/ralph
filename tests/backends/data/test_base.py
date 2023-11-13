"""Tests for the base data backend"""

import logging
from typing import Any, Union

import pytest

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseQuery,
    enforce_query_checks,
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
def test_backends_data_base_enforce_query_checks_with_valid_input(value, expected):
    """Test the enforce_query_checks function given valid input."""

    class MockBaseDataBackend(BaseDataBackend):
        """A class mocking the base data backend class."""

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
