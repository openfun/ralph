"""Tests for the video event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.bookmark.statements import (
    EdxBookmarkAdded,
    EdxBookmarkListed,
    EdxBookmarkRemoved,
    UIEdxBookmarkAccessed,
    UIEdxCourseToolAccessed,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


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
@custom_given(st.data())
def test_models_edx_bookmark_selectors_with_valid_statements(class_, data):
    """Test given a valid bookmark edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(EdxBookmarkAdded)
def test_models_edx_edx_bookmark_added_with_valid_statement(
    statement,
):
    """Test that a `edx.bookmark.added` statement has the expected `event_type`
    and `name`."""
    assert statement.event_type == "edx.bookmark.added"
    assert statement.name == "edx.bookmark.added"


@custom_given(EdxBookmarkListed)
def test_models_edx_edx_bookmark_listed_with_valid_statement(
    statement,
):
    """Test that a `edx.bookmark.listed` statement has the expected `event_type`
    and `name`."""
    assert statement.event_type == "edx.bookmark.listed"
    assert statement.name == "edx.bookmark.listed"


@custom_given(EdxBookmarkRemoved)
def test_models_edx_edx_bookmark_removed_with_valid_statement(
    statement,
):
    """Test that a `edx.bookmark.removed` statement has the expected `event_type`
    and `name`."""
    assert statement.event_type == "edx.bookmark.removed"
    assert statement.name == "edx.bookmark.removed"


@custom_given(UIEdxBookmarkAccessed)
def test_models_edx_ui_edx_bookmark_accessed_with_valid_statement(
    statement,
):
    """Test that a `edx.bookmark.accessed` statement has the expected `event_type`
    and `name`."""
    assert statement.event_type == "edx.bookmark.accessed"
    assert statement.name == "edx.bookmark.accessed"


@custom_given(UIEdxCourseToolAccessed)
def test_models_edx_ui_edx_course_tool_accessed_with_valid_statement(
    statement,
):
    """Test that a `edx.course.tool.accessed` statement has the expected `event_type`
    and `name`."""
    assert statement.event_type == "edx.course.tool.accessed"
    assert statement.name == "edx.course.tool.accessed"
