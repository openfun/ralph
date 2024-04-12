"""Tests for the peer_instruction event models."""

import json

import pytest

from ralph.models.edx.notes.statements import (
    UIEdxCourseStudentNotesAdded,
    UIEdxCourseStudentNotesDeleted,
    UIEdxCourseStudentNotesEdited,
    UIEdxCourseStudentNotesNotesPageViewed,
    UIEdxCourseStudentNotesSearched,
    UIEdxCourseStudentNotesUsedUnitLink,
    UIEdxCourseStudentNotesViewed,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
        UIEdxCourseStudentNotesAdded,
        UIEdxCourseStudentNotesDeleted,
        UIEdxCourseStudentNotesEdited,
        UIEdxCourseStudentNotesNotesPageViewed,
        UIEdxCourseStudentNotesSearched,
        UIEdxCourseStudentNotesUsedUnitLink,
        UIEdxCourseStudentNotesViewed,
    ],
)
def test_models_notes_selectors_with_valid_statements(class_):
    """Test given a valid notes edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_ui_edx_course_student_notes_added_with_valid_statement():
    """Test that a `edx.course.student_notes.added` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseStudentNotesAdded)
    assert statement.event_type == "edx.course.student_notes.added"
    assert statement.name == "edx.course.student_notes.added"


def test_models_edx_ui_edx_course_student_notes_deleted_with_valid_statement():
    """Test that a `edx.course.student_notes.deleted` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseStudentNotesDeleted)
    assert statement.event_type == "edx.course.student_notes.deleted"
    assert statement.name == "edx.course.student_notes.deleted"


def test_models_edx_ui_edx_course_student_notes_edited_with_valid_statement():
    """Test that a `edx.course.student_notes.edited` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseStudentNotesEdited)
    assert statement.event_type == "edx.course.student_notes.edited"
    assert statement.name == "edx.course.student_notes.edited"


def test_models_edx_ui_edx_course_student_notes_searched_with_valid_statement():
    """Test that a `edx.course.student_notes.searched` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseStudentNotesSearched)
    assert statement.event_type == "edx.course.student_notes.searched"
    assert statement.name == "edx.course.student_notes.searched"


def test_models_edx_ui_edx_course_student_notes_notes_page_viewed_with_valid_statement():  # noqa: E501
    """Test that a `edx.course.student_notes.notes_page_viewed` statement has
    the expected `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseStudentNotesNotesPageViewed)
    assert statement.event_type == "edx.course.student_notes.notes_page_viewed"
    assert statement.name == "edx.course.student_notes.notes_page_viewed"


def test_models_edx_ui_edx_course_student_notes_used_unit_link_with_valid_statement():
    """Test that a `edx.course.student_notes.used_unit_link` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseStudentNotesUsedUnitLink)
    assert statement.event_type == "edx.course.student_notes.used_unit_link"
    assert statement.name == "edx.course.student_notes.used_unit_link"


def test_models_edx_ui_edx_course_student_notes_viewed_with_valid_statement():
    """Test that a `edx.course.student_notes.viewed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseStudentNotesViewed)
    assert statement.event_type == "edx.course.student_notes.viewed"
    assert statement.name == "edx.course.student_notes.viewed"
