"""Tests for the xAPI verb fields"""

import json

from ralph.models.xapi.fields.verb import PageTerminatedVerbField, PageViewedVerbField


def test_models_xapi_fields_verb_page_viewed_verb_field():
    """Tests that the PageViewedVerbField returns the expected dictionary."""

    assert json.loads(PageViewedVerbField().json()) == {
        "id": "http://id.tincanapi.com/verb/viewed",
        "display": {"en": "viewed"},
    }


def test_models_xapi_fields_verb_page_terminated_verb_field():
    """Tests that the PageTerminatedVerbField returns the expected dictionary."""

    assert json.loads(PageTerminatedVerbField().json()) == {
        "id": "http://adlnet.gov/expapi/verbs/terminated",
        "display": {"en": "terminated"},
    }
