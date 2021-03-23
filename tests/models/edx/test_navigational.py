"""Tests for the navigational event models"""

import json
import re

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.base import BaseContextField
from ralph.models.edx.navigational import (
    NavigationalEventField,
    UIPageClose,
    UISeqGoto,
    UISeqNext,
    UISeqPrev,
)
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(st.builds(UIPageClose, referer=provisional.urls(), page=provisional.urls()))
def test_models_edx_ui_page_close_selector_with_valid_event(event):
    """Tests given a page_close event the get_model method should return UIPageClose model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is UIPageClose


@settings(max_examples=1)
@given(st.builds(NavigationalEventField))
def test_fields_edx_navigational_events_event_field_with_valid_content(field):
    """Tests that a valid NavigationalEventField field does not raise a ValidationError."""

    assert re.match(
        r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@sequential\+block@[a-f0-9]{32}$",
        field.id,
    )


@pytest.mark.parametrize(
    "id",
    [
        "block-v2:orgX=CS111+20_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1",
        "block-v1:orgX=CS11120_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea1",
        "block-v1:orgX=CS111=20_T1+tipe@sequential+block@d0d4a647742943e3951b45d9db8a0ea1",
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        "block-v1:orgX=CS111=20_T1+type@sequential+block@d0d4a647742943z3951b45d9db8a0ea1",
        "block-v1:orgX=CS111=20_T1+type@sequential+block@d0d4a647742943e3951b45d9db8a0ea13",
    ],  # pylint: disable=invalid-name
)
@settings(max_examples=1)
@given(st.builds(NavigationalEventField))
def test_fields_edx_navigational_events_event_field_with_invalid_content(
    id, event  # pylint: disable=redefined-builtin
):
    """Tests that an invalid NavigationalEventField field raises a ValidationError."""

    invalid_event = json.loads(event.json())
    invalid_event["id"] = id

    with pytest.raises(ValidationError, match="id\n  string does not match regex"):
        NavigationalEventField(**invalid_event)


@settings(max_examples=1)
@given(
    st.builds(
        UISeqGoto,
        context=st.builds(BaseContextField),
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(NavigationalEventField),
    )
)
def test_models_edx_ui_seq_goto_selector_with_valid_event(event):
    """Tests given a seq_goto event the get_model method should return UISeqGoto model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is UISeqGoto


@settings(max_examples=1)
@given(
    st.builds(
        UISeqNext,
        context=st.builds(BaseContextField),
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(
            NavigationalEventField, old=st.integers(0, 0), new=st.integers(1, 1)
        ),
    )
)
def test_models_edx_ui_seq_next_selector_with_valid_event(event):
    """Tests given a seq_next event the get_model method should return UISeqNext model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is UISeqNext


@pytest.mark.parametrize("old,new", [("0", "10"), ("10", "0")])
@settings(max_examples=1)
@given(
    st.builds(
        UISeqNext,
        context=st.builds(BaseContextField),
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(
            NavigationalEventField, old=st.integers(0, 0), new=st.integers(1, 1)
        ),
    )
)
def test_models_edx_ui_seq_next_event_with_invalid_content(old, new, event):
    """Tests that an invalid seq_next event raises a ValidationError."""

    invalid_event = json.loads(event.json())
    invalid_event["event"]["old"] = old
    invalid_event["event"]["new"] = new

    with pytest.raises(
        ValidationError,
        match="event\n  event.new - event.old should be equal to 1",
    ):
        UISeqNext(**invalid_event)


@settings(max_examples=1)
@given(
    st.builds(
        UISeqPrev,
        context=st.builds(BaseContextField),
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(
            NavigationalEventField, old=st.integers(1, 1), new=st.integers(0, 0)
        ),
    )
)
def test_models_edx_ui_seq_prev_selector_with_valid_event(event):
    """Tests given a seq_prev event the get_model method should return UISeqPrev model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is UISeqPrev


@pytest.mark.parametrize("old,new", [("0", "10"), ("10", "0")])
@settings(max_examples=1)
@given(
    st.builds(
        UISeqPrev,
        context=st.builds(BaseContextField),
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(
            NavigationalEventField, old=st.integers(1, 1), new=st.integers(0, 0)
        ),
    )
)
def test_models_edx_ui_seq_prev_event_with_invalid_content(old, new, event):
    """Tests that an invalid seq_prev event raises a ValidationError."""

    invalid_event = json.loads(event.json())
    invalid_event["event"]["old"] = old
    invalid_event["event"]["new"] = new

    with pytest.raises(
        ValidationError, match="event\n  event.old - event.new should be equal to 1"
    ):
        UISeqPrev(**invalid_event)
