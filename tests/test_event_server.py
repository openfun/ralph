"""
Tests for the Server event schema
"""
# pylint: disable=redefined-outer-name
import pandas as pd
import pytest
from marshmallow import ValidationError

from ralph.schemas.edx.server import ServerEventSchema

from .fixtures.logs import EventType, _event

SCHEMA = ServerEventSchema()


@pytest.fixture()
def server_event():
    """Returns a server event generator that generates size number of events"""
    return lambda size, **kwargs: _event(size, EventType.SERVER, **kwargs)


def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid server events does not raise exceptions"""
    chunks = pd.read_json("tests/data/server_event.log", lines=True, dtype=False)
    try:
        for _, chunk in chunks.iterrows():
            SCHEMA.load(chunk.to_dict())
    except ValidationError:
        pytest.fail("valid server events should not raise exceptions")


def test_valid_event_type_should_not_raise_exception(server_event):
    """Test that a valid event_type does not raise a ValidationError"""
    try:
        server_event(1)
        server_event(1, event_type="/", context_args={"path": "/"})
        server_event(
            1, event_type="/a/valid/path", context_args={"path": "/a/valid/path"}
        )
    except ValidationError:
        pytest.fail("Valid server event event_type should not raise exceptions")


def test_invalid_event_type_should_raise_exception(server_event):
    """Test that a invalid event_type raise ValidationError"""
    with pytest.raises(ValidationError):
        server_event(1, event_type="/path/not/equal/to/context/path")
    with pytest.raises(ValidationError):
        server_event(
            1, event_type="invalid/path", context_args={"path": "invalid/path"}
        )
    with pytest.raises(ValidationError):
        server_event(1, event_type=123, context_args={"path": 123})
    with pytest.raises(ValidationError):
        server_event(1, event_type={}, context_args={"path": {}})


def test_valid_event_field_should_not_raise_exception(server_event):
    """Test that a valid event field does not raise a ValidationError"""
    try:
        server_event(1, event='{"POST": {"key": ["value"]}, "GET": {}}')
        server_event(1, event='{"POST": {}, "GET": {}}')
    except ValidationError:
        pytest.fail("Valid server event event_type should not raise exceptions")


def test_invalid_event_field_should_raise_exception(server_event):
    """Test that a invalid event_type raise ValidationError"""
    with pytest.raises(ValidationError):
        server_event(1, event="")
    with pytest.raises(ValidationError):
        server_event(1, event='{"POST": {}}')
    with pytest.raises(ValidationError):
        server_event(1, event='{"GET": {}}')
    with pytest.raises(ValidationError):
        server_event(1, event='{"POST": {}, "GET": {}, "NOT_POST_NOR_GET": {}}')
    with pytest.raises(ValidationError):
        server_event(1, event='{"POST": "not_object", "GET": {}}')
    with pytest.raises(ValidationError):
        server_event(1, event='{"POST": {}, "GET": "not_object"')
    with pytest.raises(ValidationError):
        server_event(1, event='{"POST": 123, "GET": {}}')
    with pytest.raises(ValidationError):
        server_event(1, event='{"POST": {}, "GET": 123')
