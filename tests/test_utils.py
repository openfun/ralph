"""Tests for Ralph utils"""


import pytest

from ralph import utils as ralph_utils
from ralph.backends import BackendTypes
from ralph.backends.database import ESDatabase
from ralph.backends.storage.ldp import LDPStorage

from .fixtures.backends import NamedClassEnum


def test_import_string():
    """Test import_string utility taken from Django utilities."""

    with pytest.raises(ImportError, match="foo doesn't look like a module path"):
        ralph_utils.import_string("foo")

    with pytest.raises(
        ImportError, match='Module "requests" does not define a "foo" attribute/class'
    ):
        ralph_utils.import_string("requests.foo")

    http_status = ralph_utils.import_string("http.HTTPStatus")
    assert http_status.OK == 200


def test_get_backend_type():
    """Test get_backend_type utility."""

    class TestBackend:
        """Dumb test backend that does not inherit from a supported backend type."""

    assert ralph_utils.get_backend_type(ESDatabase) == BackendTypes.DATABASE
    assert ralph_utils.get_backend_type(LDPStorage) == BackendTypes.STORAGE
    assert ralph_utils.get_backend_type(TestBackend) is None


def test_get_class_names():
    """Test get_class_names utility."""

    assert ralph_utils.get_class_names([module.value for module in NamedClassEnum]) == [
        "A",
        "B",
    ]


def test_get_class_from_name():
    """Test get_class_from_name utility."""

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


def test_get_instance_from_class():
    """Test get_instance_from_class utility."""

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
