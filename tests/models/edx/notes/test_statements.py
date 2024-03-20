"""Tests for the peer_instruction event models."""

import json

import pytest
from hypothesis import strategies as st

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

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


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
@custom_given(st.data())
def test_models_notes_selectors_with_valid_statements(class_, data):
    """Test given a valid notes edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(UIEdxCourseStudentNotesAdded)
def test_models_edx_ui_edx_course_student_notes_added_with_valid_statement(
    statement,
):
    """Test that a `edx.course.student_notes.added` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.course.student_notes.added"
    assert statement.name == "edx.course.student_notes.added"


@custom_given(UIEdxCourseStudentNotesDeleted)
def test_models_edx_ui_edx_course_student_notes_deleted_with_valid_statement(
    statement,
):
    """Test that a `edx.course.student_notes.deleted` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.course.student_notes.deleted"
    assert statement.name == "edx.course.student_notes.deleted"


@custom_given(UIEdxCourseStudentNotesEdited)
def test_models_edx_ui_edx_course_student_notes_edited_with_valid_statement(
    statement,
):
    """Test that a `edx.course.student_notes.edited` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.course.student_notes.edited"
    assert statement.name == "edx.course.student_notes.edited"


@custom_given(UIEdxCourseStudentNotesSearched)
def test_models_edx_ui_edx_course_student_notes_searched_with_valid_statement(
    statement,
):
    """Test that a `edx.course.student_notes.searched` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.course.student_notes.searched"
    assert statement.name == "edx.course.student_notes.searched"


@custom_given(UIEdxCourseStudentNotesNotesPageViewed)
def test_models_edx_ui_edx_course_student_notes_notes_page_viewed_with_valid_statement(
    statement,
):
    """Test that a `edx.course.student_notes.notes_page_viewed` statement has
    the expected `event_type` and `name`.
    """
    assert statement.event_type == "edx.course.student_notes.notes_page_viewed"
    assert statement.name == "edx.course.student_notes.notes_page_viewed"


@custom_given(UIEdxCourseStudentNotesUsedUnitLink)
def test_models_edx_ui_edx_course_student_notes_used_unit_link_with_valid_statement(
    statement,
):
    """Test that a `edx.course.student_notes.used_unit_link` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.course.student_notes.used_unit_link"
    assert statement.name == "edx.course.student_notes.used_unit_link"


@custom_given(UIEdxCourseStudentNotesViewed)
def test_models_edx_ui_edx_course_student_notes_viewed_with_valid_statement(
    statement,
):
    """Test that a `edx.course.student_notes.viewed` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.course.student_notes.viewed"
    assert statement.name == "edx.course.student_notes.viewed"
