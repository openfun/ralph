"""Tests for Ralph utils"""

import pytest

from ralph import utils as ralph_utils
from ralph.backends import BackendTypes
from ralph.defaults import Settings

from .fixtures.backends import NamedClassEnum


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

    assert Settings.get_backend_type("es") == BackendTypes.DATABASE
    assert Settings.get_backend_type("ldp") == BackendTypes.STORAGE
    assert Settings.get_backend_type("ws") == BackendTypes.STREAM
    assert Settings.get_backend_type("TestBackend") is None


def test_utils_get_class_names():
    """Tests get_class_names utility."""

    assert ralph_utils.get_class_names([module.value for module in NamedClassEnum]) == [
        "A",
        "B",
    ]


def test_utils_get_class_from_name():
    """Tests get_class_from_name utility."""

    assert (
        ralph_utils.get_class_from_name(
            "A", [module.value for module in NamedClassEnum]
        ).name
        == "A"
    )
    assert (
        ralph_utils.get_class_from_name(
            "B", [module.value for module in NamedClassEnum]
        ).name
        == "B"
    )
    with pytest.raises(ImportError, match="C class is not available"):
        assert (
            ralph_utils.get_class_from_name(
                "C", [module.value for module in NamedClassEnum]
            ).name
            == "B"
        )


def test_utils_get_instance_from_class():
    """Tests get_instance_from_class utility."""

    class NamedTestClass:
        """Named test class."""

        name = "test"

        def __init__(self, force=False, verbose=0):
            self.force = force
            self.verbose = verbose

    test = ralph_utils.get_instance_from_class(
        NamedTestClass, test_force=True, test_verbose=2
    )
    assert test.force
    assert test.verbose == 2

    # Extra parameters are ignored
    test = ralph_utils.get_instance_from_class(
        NamedTestClass, test_force=True, test_verbose=2, misc=True
    )
    assert test.force
    assert test.verbose == 2


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
