"""Tests for the xAPI verb fields."""

import json

from ralph.models.xapi.fields.verbs import TerminatedVerbField, ViewedVerbField


def test_models_xapi_fields_verb_viewed_verb_field():
    """Tests that the ViewedVerbField returns the expected dictionary."""
    assert json.loads(ViewedVerbField().json()) == {
        "id": "http://id.tincanapi.com/verb/viewed",
        "display": {"en-US": "viewed"},
    }


def test_models_xapi_fields_verb_terminated_verb_field():
    """Tests that the TerminatedVerbField returns the expected dictionary."""
    assert json.loads(TerminatedVerbField().json()) == {
        "id": "http://adlnet.gov/expapi/verbs/terminated",
        "display": {"en-US": "terminated"},
    }
