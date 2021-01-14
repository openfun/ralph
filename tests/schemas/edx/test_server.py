"""Tests for the Server event schema"""

# pylint: disable=redefined-outer-name
import pytest
from marshmallow import ValidationError

from tests.fixtures.logs import EventType, event_generator

from .test_common import check_error


@pytest.fixture()
def server_event():
    """Return a server event generator that generates size number of events"""

    return lambda **kwargs: event_generator(EventType.SERVER, **kwargs)


def test_valid_event_type_should_not_raise_exception(server_event):
    """Test that a valid event_type does not raise a ValidationError"""

    try:
        server_event()
        server_event(event_type="/", context_args={"path": "/"})
        server_event(event_type="/a/valid/path", context_args={"path": "/a/valid/path"})
    except ValidationError:
        pytest.fail("Valid server event event_type should not raise exceptions")


def test_invalid_event_type_should_raise_exception(server_event):
    """Test that a invalid event_type raise ValidationError"""

    with pytest.raises(ValidationError) as excinfo:
        server_event(event_type="/path/not/equal/to/context/path")
    check_error(excinfo, "event_type should be equal to context.path")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event_type="invalid/path", context_args={"path": "invalid/path"})
    check_error(excinfo, "Not a valid URL.")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event_type=123, context_args={"path": 123})
    check_error(excinfo, "Not a valid URL.")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event_type={}, context_args={"path": {}})
    check_error(excinfo, "Not a valid URL.")


def test_valid_event_field_should_not_raise_exception(server_event):
    """Test that a valid event field does not raise a ValidationError"""

    try:
        server_event(event='{"POST": {"key": ["value"]}, "GET": {}}')
        server_event(event='{"POST": {}, "GET": {}}')
    except ValidationError:
        pytest.fail("Valid server event event_type should not raise exceptions")


def test_invalid_event_field_should_raise_exception(server_event):
    """Test that a invalid event_type raise ValidationError"""

    with pytest.raises(ValidationError) as excinfo:
        server_event(event="")
    check_error(excinfo, "Server event should contain a JSON string")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"POST": {}}')
    check_error(excinfo, "Server event field should exactly have two keys")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"GET": {}}')
    check_error(excinfo, "Server event field should exactly have two keys")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"GET": {}, "NOT_POST": {}}')
    check_error(excinfo, "Server event should contain GET and POST keys")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"POST": {}, "GET": {}, "NOT_POST_NOR_GET": {}}')
    check_error(excinfo, "Server event field should exactly have two keys")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"POST": "not_object", "GET": {}}')
    check_error(
        excinfo, "Server event GET and POST values should be serialized objects"
    )
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"POST": {}, "GET": "not_object"')
    check_error(excinfo, "Server event should contain a JSON string")
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"POST": 123, "GET": {}}')
    check_error(
        excinfo, "Server event GET and POST values should be serialized objects"
    )
    with pytest.raises(ValidationError) as excinfo:
        server_event(event='{"POST": {}, "GET": 123')
    check_error(excinfo, "Server event should contain a JSON string")
