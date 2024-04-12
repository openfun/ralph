"""Tests for notes models event fields."""

import json

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.notes.fields.events import (
    NotesEventField,
    UIEdxCourseStudentNotesEditedEventField,
    UIEdxCourseStudentNotesUsedUnitLinkEventField,
)

from tests.factories import mock_instance


def test_models_edx_notes_event_field_with_valid_field():
    """Test that a valid `NotesEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(NotesEventField)
    assert len(field.note_text) <= 8333
    assert all(
        value
        in ["note_text", "highlighted_content", "tags", "old_note_text", "old_tags"]
        for value in field.truncated
    )


def test_models_edx_notes_event_field_with_invalid_note_text():
    """Test that a valid `NotesEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(NotesEventField)
    invalid_field = json.loads(field.json())
    invalid_field["note_text"] = "x" * 8334
    with pytest.raises(
        ValidationError,
        match="note_text\n  String should have at most 8333 characters",
    ):
        NotesEventField(**invalid_field)


@pytest.mark.parametrize("truncated", ["notetext", "highlightedcontent", "tag"])
def test_models_edx_notes_event_field_with_invalid_truncated(truncated):
    """Test that an invalid `NotesEventField` raises a `ValidationError`."""

    field = mock_instance(NotesEventField)
    invalid_field = json.loads(field.json())
    invalid_field["truncated"] = truncated

    with pytest.raises(
        ValidationError, match="truncated\n  Input should be a valid list"
    ):
        NotesEventField(**invalid_field)


def test_models_edx_ui_edx_course_student_notes_edited_event_field_with_valid_field():
    """Test that a valid `UIEdxCourseStudentNotesEditedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(UIEdxCourseStudentNotesEditedEventField)
    assert len(field.old_note_text) <= 8333


def test_models_edx_ui_edx_course_student_notes_edited_event_field_with_invalid_old_note_text():  # noqa: E501
    """Test that a valid `EdxCourseStudentNotesEditedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(UIEdxCourseStudentNotesEditedEventField)
    invalid_field = json.loads(field.json())
    invalid_field["old_note_text"] = "x" * 8334
    with pytest.raises(
        ValidationError,
        match="old_note_text\n  String should have at most 8333 characters",
    ):
        UIEdxCourseStudentNotesEditedEventField(**invalid_field)


def test_models_edx_ui_edx_course_student_notes_used_unit_link_event_field_with_valid_field():  # noqa: E501
    """Test that a valid `UIEdxCourseStudentNotesUsedUnitLinkEventField` does
    not raise a `ValidationError`.
    """
    field = mock_instance(UIEdxCourseStudentNotesUsedUnitLinkEventField)
    assert field.view in ("Recent Activity", "Search Results")


@pytest.mark.parametrize("view", ["recent activity", "search results"])
def test_models_edx_ui_edx_course_student_notes_used_unit_link_event_field_with_invalid_view(  # noqa: E501
    view,
):
    """Test that an invalid `UIEdxCourseStudentNotesUsedUnitLinkEventField` raises
    a `ValidationError`.
    """
    field = mock_instance(UIEdxCourseStudentNotesUsedUnitLinkEventField)

    invalid_field = json.loads(field.json())
    invalid_field["view"] = view

    with pytest.raises(ValidationError, match="view"):
        UIEdxCourseStudentNotesUsedUnitLinkEventField(**invalid_field)
