"""Tests for Ralph utils"""


import pytest

from ralph import utils as ralph_utils

from .fixtures.backends import NamedClassEnum


def test_import_string():
    """Test import_string utility taken from Django utilities"""

    with pytest.raises(ImportError, match="foo doesn't look like a module path"):
        ralph_utils.import_string("foo")

    with pytest.raises(
        ImportError, match='Module "requests" does not define a "foo" attribute/class'
    ):
        ralph_utils.import_string("requests.foo")

    http_status = ralph_utils.import_string("http.HTTPStatus")
    assert http_status.OK == 200


def test_get_class_from_name():
    """Test get_class_from_name utility"""

    assert ralph_utils.get_class_from_name("A", NamedClassEnum).name == "A"
    assert ralph_utils.get_class_from_name("B", NamedClassEnum).name == "B"
    with pytest.raises(ImportError, match="C class is not available"):
        assert ralph_utils.get_class_from_name("C", NamedClassEnum).name == "B"


def test_get_instance_from_class():
    """Test get_instance_from_class utility"""

    class NamedTestClass:
        """Named test class"""

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
