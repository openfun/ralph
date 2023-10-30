"""Tests for Ralph utils."""

import logging

import pytest
from pydantic import BaseModel

from ralph import utils as ralph_utils
from ralph.exceptions import UnsupportedBackendException


def test_utils_import_string():
    """Test import_string utility taken from Django utilities."""
    with pytest.raises(ImportError, match="foo doesn't look like a module path"):
        ralph_utils.import_string("foo")

    with pytest.raises(
        ImportError, match='Module "requests" does not define a "foo" attribute/class'
    ):
        ralph_utils.import_string("requests.foo")

    http_status = ralph_utils.import_string("http.HTTPStatus")
    assert http_status.OK == 200


def test_utils_get_backend_class(caplog):
    """Test the `get_backend_class` utility should return the expected result."""
    backends = {"es": type("es_backend", (), {}), "fs": type("fs_backend", (), {})}
    assert ralph_utils.get_backend_class(backends, "es") == backends["es"]
    assert ralph_utils.get_backend_class(backends, "fs") == backends["fs"]
    msg = "'foo' backend not found in available backends: es, fs"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(UnsupportedBackendException, match=msg):
            ralph_utils.get_backend_class(backends, "foo")

    assert ("ralph.utils", logging.ERROR, msg) in caplog.record_tuples


@pytest.mark.parametrize(
    "options,expected",
    [
        # Empty options should produce default result.
        ({}, {"FOO": "FOO"}),
        # Options not matching the backend name are ignored.
        ({"foo": "bar", "not_dummy_foo": "baz"}, {"FOO": "FOO"}),
        # Options matching the backend name update the defaults.
        ({"dummy_foo": "bar"}, {"FOO": "bar"}),
    ],
)
def test_utils_get_backend_instance(options, expected):
    """Test the `get_backend_instance` utility should return the expected result."""

    class DummyTestBackendSettings(BaseModel):
        """Represent a dummy backend setting."""

        FOO: str = "FOO"

    class DummyTestBackend:
        """Represent a dummy backend instance."""

        name = "dummy"
        settings_class = DummyTestBackendSettings

        def __init__(self, settings):
            self.settings = settings

    backend = ralph_utils.get_backend_instance(DummyTestBackend, options)
    assert isinstance(backend, DummyTestBackend)
    assert backend.settings.dict() == expected


@pytest.mark.parametrize("path,value", [(["foo", "bar"], "bar_value")])
def test_utils_get_dict_value_from_path_should_return_given_value(path, value):
    """Test the get_dict_value_from_path function should return the value when it's
    present.
    """
    dictionary = {"foo": {"bar": "bar_value"}}
    assert ralph_utils.get_dict_value_from_path(dictionary, path) == value


@pytest.mark.parametrize(
    "path",
    [
        ["foo", "bar", "baz", "qux"],
        ["foo", "not_bar"],
        ["not_foo", "bar"],
        None,
    ],
)
def test_utils_get_dict_value_from_path_should_return_none_when_value_does_not_exists(
    path,
):
    """Test the get_dict_value_from_path function should return None if the value is
    not found.
    """
    dictionary = {"foo": {"bar": "bar_value"}}
    assert ralph_utils.get_dict_value_from_path(dictionary, path) is None


def test_utils_set_dict_value_from_path_creating_new_fields():
    """Test when the fields are not present, set_dict_value_from_path should add
    them.
    """
    dictionary = {}
    ralph_utils.set_dict_value_from_path(dictionary, ["foo", "bar"], "baz")
    assert dictionary == {"foo": {"bar": "baz"}}


def test_utils_set_dict_value_from_path_updating_fields():
    """Test when the fields are present, set_dict_value_from_path should update
    them.
    """
    dictionary = {"foo": {"bar": "bar_value"}}
    ralph_utils.set_dict_value_from_path(dictionary, ["foo", "bar"], "baz")
    assert dictionary == {"foo": {"bar": "baz"}}
