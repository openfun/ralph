"""Tests for the server event model"""

import pytest
from pydantic.error_wrappers import ValidationError

from tests.fixtures.edx.server import ServerEventFactory


@pytest.mark.parametrize(
    "kwargs",
    [
        {"context__path": "/", "event_type": "/"},
        {"context__path": "/a/valid/path", "event_type": "/a/valid/path"},
        {"event": '{"POST": {"key": ["value"]}, "GET": {}}'},
        {"event": '{"POST": {}, "GET": {}}'},
    ],
)
def test_models_edx_server_event_with_valid_content(kwargs):
    """Tests that a valid server event does not raise a ValidationError."""

    try:
        ServerEventFactory(**kwargs)
    except ValidationError:
        pytest.fail(f"Valid server event with {kwargs} should not raise exceptions")


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"event_type": 123}, "value is not a valid path"),
        ({"event_type": {}}, "value is not a valid path"),
        ({"context__path": 123}, "value is not a valid path"),
        ({"context__path": {}}, "value is not a valid path"),
        ({"event_type": "/not/context"}, "event_type should be equal to context.path"),
        ({"event": "not JSON"}, "must be a JSON string"),
        ({"event": '{"POST": {}}'}, "GET field should exist"),
        ({"event": '{"GET": {}}'}, "POST field should exist"),
        ({"event": '{"GET": {}, "NOT_POST": {}}'}, "POST field should exist"),
        ({"event": '{"POST": {}, "GET": {}, "NOR": {}}'}, "extra fields not permitted"),
        ({"event": '{"POST": "not_object", "GET": {}}'}, "value must be a dict"),
        ({"event": '{"POST": {}, "GET": "not_object"}'}, "value must be a dict"),
        ({"event": '{"POST": 123, "GET": {}}'}, "value must be a dict"),
        ({"event": '{"POST": {}, "GET": 123}'}, "value must be a dict"),
    ],
)
def test_models_edx_server_event_with_invalid_content(kwargs, error):
    """Tests that an invalid server event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        ServerEventFactory(**kwargs)
