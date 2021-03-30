"""Tests for the browser event models"""

import json
import re

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st
from pydantic.error_wrappers import ValidationError

from ralph.exceptions import UnknownEventException
from ralph.models.edx.browser import BaseBrowserEvent, PageClose
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(st.builds(BaseBrowserEvent, referer=provisional.urls(), page=provisional.urls()))
def test_models_edx_browser_base_browser_event_with_valid_content(event):
    """Tests that a valid base browser event does not raise a ValidationError."""

    assert re.match(r"^[a-f0-9]{32}$", event.session) or event.session == ""


@pytest.mark.parametrize(
    "session,error",
    [
        # less than 32 characters
        ("abcdef0123456789", "session\n  string does not match regex"),
        # more than 32 characters
        ("abcdef0123456789abcdef0123456789abcdef", "string does not match regex"),
        # with excluded characters
        ("abcdef0123456789_abcdef012345678", "string does not match regex"),
    ],
)
@settings(max_examples=1)
@given(st.builds(BaseBrowserEvent, referer=provisional.urls(), page=provisional.urls()))
def test_models_edx_browser_base_browser_event_with_invalid_content(
    session, error, event
):
    """Tests that a valid base browser event raises a ValidationError."""

    invalid_event = json.loads(event.json())
    invalid_event["session"] = session

    with pytest.raises(ValidationError, match=error):
        BaseBrowserEvent(**invalid_event)


@settings(max_examples=1)
@given(st.builds(PageClose, referer=provisional.urls(), page=provisional.urls()))
def test_models_selector_model_selector_get_model_with_valid_event(event):
    """Tests given a page_close event the get_model method should return PageClose model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is PageClose


def test_models_selector_model_selector_get_model_with_invalid_event():
    """Tests given a page_close event the get_model method should raise UnknownEventException."""

    with pytest.raises(UnknownEventException):
        ModelSelector(module="ralph.models.edx").get_model({"invalid": "event"})
