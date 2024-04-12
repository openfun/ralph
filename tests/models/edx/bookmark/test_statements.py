"""Tests for the video event models."""

import json

import pytest

from ralph.models.edx.bookmark.statements import (
    EdxBookmarkAdded,
    EdxBookmarkListed,
    EdxBookmarkRemoved,
    UIEdxBookmarkAccessed,
    UIEdxCourseToolAccessed,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
        EdxBookmarkAdded,
        EdxBookmarkListed,
        EdxBookmarkRemoved,
        UIEdxBookmarkAccessed,
        UIEdxCourseToolAccessed,
    ],
)
def test_models_edx_bookmark_selectors_with_valid_statements(class_):
    """Test given a valid bookmark edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_bookmark_added_with_valid_statement():
    """Test that a `edx.bookmark.added` statement has the expected `event_type`
    and `name`."""
    statement = mock_instance(EdxBookmarkAdded)
    assert statement.event_type == "edx.bookmark.added"
    assert statement.name == "edx.bookmark.added"


def test_models_edx_edx_bookmark_listed_with_valid_statement():
    """Test that a `edx.bookmark.listed` statement has the expected `event_type`
    and `name`."""
    statement = mock_instance(EdxBookmarkListed)
    assert statement.event_type == "edx.bookmark.listed"
    assert statement.name == "edx.bookmark.listed"


def test_models_edx_edx_bookmark_removed_with_valid_statement():
    """Test that a `edx.bookmark.removed` statement has the expected `event_type`
    and `name`."""
    statement = mock_instance(EdxBookmarkRemoved)
    assert statement.event_type == "edx.bookmark.removed"
    assert statement.name == "edx.bookmark.removed"


def test_models_edx_ui_edx_bookmark_accessed_with_valid_statement():
    """Test that a `edx.bookmark.accessed` statement has the expected `event_type`
    and `name`."""
    statement = mock_instance(UIEdxBookmarkAccessed)
    assert statement.event_type == "edx.bookmark.accessed"
    assert statement.name == "edx.bookmark.accessed"


def test_models_edx_ui_edx_course_tool_accessed_with_valid_statement():
    """Test that a `edx.course.tool.accessed` statement has the expected `event_type`
    and `name`."""
    statement = mock_instance(UIEdxCourseToolAccessed)
    assert statement.event_type == "edx.course.tool.accessed"
    assert statement.name == "edx.course.tool.accessed"
