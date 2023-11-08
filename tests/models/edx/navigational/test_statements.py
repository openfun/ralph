"""Tests for the navigational event models."""

import json
import re

import pytest
from hypothesis import strategies as st
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.navigational.fields.events import NavigationalEventField
from ralph.models.edx.navigational.statements import (
    UIPageClose,
    UISeqGoto,
    UISeqNext,
    UISeqPrev,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [
        UIPageClose,
        UISeqGoto,
        UISeqNext,
        UISeqPrev,
    ],
)
@custom_given(st.data())
def test_models_edx_navigational_selectors_with_valid_statements(class_, data):
    """Test given a valid navigational edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(NavigationalEventField)
def test_fields_edx_navigational_events_event_field_with_valid_content(field):
    """Test that a valid `NavigationalEventField` does not raise a
    `ValidationError`.
    """
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@sequential\+block@[a-f0-9]{32}$"
        ),
        field.id,
    )


@pytest.mark.parametrize(
    "id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
@custom_given(NavigationalEventField)
def test_fields_edx_navigational_events_event_field_with_invalid_content(id, field):
    """Test that an invalid `NavigationalEventField` raises a `ValidationError`."""
    invalid_field = json.loads(field.json())
    invalid_field["id"] = id

    with pytest.raises(ValidationError, match="id\n  string does not match regex"):
        NavigationalEventField(**invalid_field)


@custom_given(UIPageClose)
def test_models_edx_ui_page_close_with_valid_statement(statement):
    """Test that a `page_close` statement has the expected `event`, `event_type` and
    `name`.
    """
    assert statement.event == "{}"
    assert statement.event_type == "page_close"
    assert statement.name == "page_close"


@custom_given(UISeqGoto)
def test_models_edx_ui_seq_goto_with_valid_statement(statement):
    """Test that a `seq_goto` statement has the expected `event_type` and `name`."""
    assert statement.event_type == "seq_goto"
    assert statement.name == "seq_goto"


@custom_given(UISeqNext)
def test_models_edx_ui_seq_next_with_valid_statement(statement):
    """Test that a `seq_next` statement has the expected `event_type` and `name`."""
    assert statement.event_type == "seq_next"
    assert statement.name == "seq_next"


@pytest.mark.parametrize("old,new", [("0", "10"), ("10", "0")])
@custom_given(UISeqNext)
def test_models_edx_ui_seq_next_with_invalid_statement(old, new, event):
    """Test that an invalid `seq_next` event raises a ValidationError."""
    invalid_event = json.loads(event.json())
    invalid_event["event"]["old"] = old
    invalid_event["event"]["new"] = new

    with pytest.raises(
        ValidationError,
        match="event\n  event.new - event.old should be equal to 1",
    ):
        UISeqNext(**invalid_event)


@custom_given(UISeqPrev)
def test_models_edx_ui_seq_prev_with_valid_statement(statement):
    """Test that a `seq_prev` statement has the expected `event_type` and `name`."""
    assert statement.event_type == "seq_prev"
    assert statement.name == "seq_prev"


@pytest.mark.parametrize("old,new", [("0", "10"), ("10", "0")])
@custom_given(UISeqPrev)
def test_models_edx_ui_seq_prev_with_invalid_statement(old, new, event):
    """Test that an invalid `seq_prev` event raises a ValidationError."""
    invalid_event = json.loads(event.json())
    invalid_event["event"]["old"] = old
    invalid_event["event"]["new"] = new

    with pytest.raises(
        ValidationError, match="event\n  event.old - event.new should be equal to 1"
    ):
        UISeqPrev(**invalid_event)
