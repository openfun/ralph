"""Tests for notes models event fields."""

import json
import sys
from typing import List

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.notes.fields.events import (
    NotesEventField,
    UIEdxCourseStudentNotesEditedEventField,
    UIEdxCourseStudentNotesUsedUnitLinkEventField,
)

from tests.fixtures.hypothesis_strategies import custom_given

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


@custom_given(NotesEventField)
def test_models_edx_notes_event_field_with_valid_field(field):
    """Test that a valid `NotesEventField` does not raise a
    `ValidationError`.
    """
    assert len(field.note_text) <= 8333
    assert field.truncated in (
        [],
        List[Literal["note_text", "highlighted_content", "tags"]],
    )


@custom_given(NotesEventField)
def test_models_edx_notes_event_field_with_invalid_note_text(field):
    """Test that a valid `NotesEventField` does not raise a
    `ValidationError`.
    """
    invalid_field = json.loads(field.json())
    invalid_field["note_text"] = "x" * 8334
    with pytest.raises(
        ValidationError,
        match="note_text\n  ensure this value has at most 8333 characters",
    ):
        NotesEventField(**invalid_field)


@pytest.mark.parametrize("truncated", ["notetext", "highlightedcontent", "tag"])
@custom_given(NotesEventField)
def test_models_edx_notes_event_field_with_invalid_truncated(truncated, field):
    """Test that an invalid `NotesEventField` raises a `ValidationError`."""

    invalid_field = json.loads(field.json())
    invalid_field["truncated"] = truncated

    with pytest.raises(ValidationError, match="truncated\n  value is not a valid list"):
        NotesEventField(**invalid_field)


@custom_given(UIEdxCourseStudentNotesEditedEventField)
def test_models_edx_ui_edx_course_student_notes_edited_event_field_with_valid_field(
    field,
):
    """Test that a valid `UIEdxCourseStudentNotesEditedEventField` does not raise a
    `ValidationError`.
    """
    assert len(field.old_note_text) <= 8333


@custom_given(UIEdxCourseStudentNotesEditedEventField)
def test_models_edx_ui_edx_course_student_notes_edited_event_field_with_invalid_old_note_text(  # noqa: E501
    field,
):
    """Test that a valid `EdxCourseStudentNotesEditedEventField` does not raise a
    `ValidationError`.
    """
    invalid_field = json.loads(field.json())
    invalid_field["old_note_text"] = "x" * 8334
    with pytest.raises(
        ValidationError,
        match="old_note_text\n  ensure this value has at most 8333 characters",
    ):
        UIEdxCourseStudentNotesEditedEventField(**invalid_field)


@custom_given(UIEdxCourseStudentNotesUsedUnitLinkEventField)
def test_models_edx_ui_edx_course_student_notes_used_unit_link_event_field_with_valid_field(  # noqa: E501
    field,
):
    """Test that a valid `UIEdxCourseStudentNotesUsedUnitLinkEventField` does
    not raise a `ValidationError`.
    """
    assert field.view in ("Recent Activity", "Search Results")


@pytest.mark.parametrize("view", ["recent activity", "search results"])
@custom_given(UIEdxCourseStudentNotesUsedUnitLinkEventField)
def test_models_edx_ui_edx_course_student_notes_used_unit_link_event_field_with_invalid_view(  # noqa: E501
    view, field
):
    """Test that an invalid `UIEdxCourseStudentNotesUsedUnitLinkEventField` raises
    a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["view"] = view

    with pytest.raises(ValidationError, match="view\n  unexpected value"):
        UIEdxCourseStudentNotesUsedUnitLinkEventField(**invalid_field)
