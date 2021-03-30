"""Tests for the base event model"""

import json
import re

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.base import BaseContextField, BaseEvent


@settings(max_examples=1)
@given(
    st.builds(
        BaseEvent, context=st.builds(BaseContextField), referer=provisional.urls()
    )
)
def test_models_edx_base_event_with_valid_content(event):
    """Tests that a valid base event does not raise a ValidationError."""

    assert len(event.username) == 0 or (len(event.username) in range(2, 31, 1))
    assert (
        re.match(r"^course-v1:.+\+.+\+.+$", event.context.course_id)
        or event.context.course_id == ""
    )


@pytest.mark.parametrize(
    "course_id,error",
    [
        (
            "course-v1:+course+not_empty",
            "course_id\n  string does not match regex",
        ),
        (
            "course-v1:org",
            "course_id\n  string does not match regex",
        ),
        (
            "course-v1:org+course",
            "course_id\n  string does not match regex",
        ),
        (
            "course-v1:org+course+",
            "course_id\n  string does not match regex",
        ),
    ],
)
@settings(max_examples=1)
@given(
    st.builds(
        BaseEvent, context=st.builds(BaseContextField), referer=provisional.urls()
    )
)
def test_models_edx_base_event_with_invalid_content(course_id, error, event):
    """Tests that a valid base event raises a ValidationError."""

    invalid_event = json.loads(event.json())
    invalid_event["context"]["course_id"] = course_id

    with pytest.raises(ValidationError, match=error):
        BaseEvent(**invalid_event)
