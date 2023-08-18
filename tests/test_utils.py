"""Tests for Ralph utils."""

from abc import ABC
from types import ModuleType

import pytest
from pydantic import BaseModel

from ralph import utils as ralph_utils
from ralph.backends.conf import backends_settings
from ralph.conf import InstantiableSettingsItem


def test_utils_import_string():
    """Tests import_string utility taken from Django utilities."""
    with pytest.raises(ImportError, match="foo doesn't look like a module path"):
        ralph_utils.import_string("foo")

    with pytest.raises(
        ImportError, match='Module "requests" does not define a "foo" attribute/class'
    ):
        ralph_utils.import_string("requests.foo")

    http_status = ralph_utils.import_string("http.HTTPStatus")
    assert http_status.OK == 200


def test_utils_get_backend_type():
    """Tests get_backend_type utility."""
    backend_types = [backend_type[1] for backend_type in backends_settings.BACKENDS]
    assert (
        ralph_utils.get_backend_type(backend_types, "es")
        == backends_settings.BACKENDS.DATA
    )
    assert (
        ralph_utils.get_backend_type(backend_types, "lrs")
        == backends_settings.BACKENDS.HTTP
    )
    assert (
        ralph_utils.get_backend_type(backend_types, "ws")
        == backends_settings.BACKENDS.STREAM
    )
    assert ralph_utils.get_backend_type(backend_types, "foo") is None


@pytest.mark.parametrize(
    "options,expected",
    [
        # Empty options should produce default result.
        ({}, {}),
        # Options not matching the backend name are ignored.
        ({"foo": "bar", "not_dummy_foo": "baz"}, {}),
    ],
)
def test_utils_get_backend_instance(monkeypatch, options, expected):
    """Tests get_backend_instance utility should return the expected result."""

    class DummyTestBackendSettings(InstantiableSettingsItem):
        """Represents a dummy backend setting."""

        FOO: str = "FOO"  # pylint: disable=disallowed-name

        def get_instance(self, **init_parameters):  # pylint: disable=no-self-use
            """Returns the init_parameters."""
            return init_parameters

    class DummyTestBackend(ABC):
        """Represents a dummy backend instance."""

        type = "test"
        name = "dummy"

        def __init__(self, *args, **kargs):  # pylint: disable=unused-argument
            return

        def __call__(self, *args, **kwargs):  # pylint: disable=unused-argument
            return {}

    def mock_import_module(*args, **kwargs):  # pylint: disable=unused-argument
        """"""
        test_module = ModuleType(name="ralph.backends.test.dummy")

        test_module.DummyTestBackendSettings = DummyTestBackendSettings
        test_module.DummyTestBackend = DummyTestBackend

        return test_module

    class TestBackendSettings(BaseModel):  # DATA-backend-type
        """A backend type including the DummyTestBackendSettings."""

        DUMMY: DummyTestBackendSettings = (
            DummyTestBackendSettings()
        )  # Es-Backend-settings

    monkeypatch.setattr(ralph_utils, "import_module", mock_import_module)
    backend_instance = ralph_utils.get_backend_instance(
        TestBackendSettings(), "dummy", options
    )
    assert isinstance(backend_instance, DummyTestBackend)
    assert backend_instance() == expected


@pytest.mark.parametrize("path,value", [(["foo", "bar"], "bar_value")])
def test_utils_get_dict_value_from_path_should_return_given_value(path, value):
    """Tests the get_dict_value_from_path function should return the value when it's
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
    """Tests the get_dict_value_from_path function should return None if the value is
    not found.
    """
    dictionary = {"foo": {"bar": "bar_value"}}
    assert ralph_utils.get_dict_value_from_path(dictionary, path) is None


def test_utils_set_dict_value_from_path_creating_new_fields():
    """Tests when the fields are not present, set_dict_value_from_path should add
    them.
    """
    dictionary = {}
    ralph_utils.set_dict_value_from_path(dictionary, ["foo", "bar"], "baz")
    assert dictionary == {"foo": {"bar": "baz"}}


def test_utils_set_dict_value_from_path_updating_fields():
    """Tests when the fields are present, set_dict_value_from_path should update
    them.
    """
    dictionary = {"foo": {"bar": "bar_value"}}
    ralph_utils.set_dict_value_from_path(dictionary, ["foo", "bar"], "baz")
    assert dictionary == {"foo": {"bar": "baz"}}
