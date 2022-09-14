"""Tests for the server event models."""

import json

import pytest

from ralph.exceptions import UnknownEventException
from ralph.models.edx.server import Server
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(Server)
def test_model_selector_server_get_model_with_valid_event(event):
    """Tests given a server statement, the get_model method should return the
    corresponding model.
    """

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is Server


def test_model_selector_server_get_model_with_invalid_event():
    """Tests given a server statement, the get_model method should raise
    UnknownEventException.
    """

    with pytest.raises(UnknownEventException):
        ModelSelector(module="ralph.models.edx").get_model({"invalid": "event"})
