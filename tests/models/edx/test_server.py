"""Tests for the server event models"""

import json

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.exceptions import UnknownEventException
from ralph.models.edx.server import Server, ServerEventField
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(st.builds(Server, referer=provisional.urls(), event=st.builds(ServerEventField)))
def test_model_selector_server_get_model_with_valid_event(event):
    """Tests given a server statement, the get_model method should return the corresponding
    model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is Server


def test_model_selector_server_get_model_with_invalid_event():
    """Tests given a server statement, the get_model method should raise UnknownEventException."""

    with pytest.raises(UnknownEventException):
        ModelSelector(module="ralph.models.edx").get_model({"invalid": "event"})
