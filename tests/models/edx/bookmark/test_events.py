"""Tests for video models event fields."""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.bookmark.fields.events import (
    EdxBookmarkAddedEventField,
    EdxBookmarkBaseEventField,
    EdxBookmarkListedEventField,
    EdxBookmarkRemovedEventField,
    UIEdxCourseToolAccessedEventField,
)

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(EdxBookmarkBaseEventField)
def test_models_edx_edx_bookmark_base_event_field_with_valid_values(field):
    """Test that a valid `EdxBookmarkBaseEventField` does not raise a
    `ValidationError`.
    """

    assert re.match(
        r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@([a-z]+)\+block@[a-f0-9]{32}$",
        field.component_usage_id,
    )
    assert field.component_type in (
        "chapter",
        "course",
        "discussion",
        "html",
        "problem",
        "sequential",
        "vertical",
        "video",
    )


@pytest.mark.parametrize(
    "component_type",
    [
        "chapte",
        "curse",
        "discusion",
        "xml",
        "probem",
        "sequencial",
        "verticel",
        "videos",
        "book",
    ],
)
@custom_given(EdxBookmarkBaseEventField)
def test_models_edx_edx_bookmark_base_event_field_with_invalid_component_type_value(
    component_type, subfield
):
    """Test that an invalid `component_type` value in
    `EdxBookmarkBaseEventField` raises a `ValidationError`.
    """
    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["component_type"] = component_type

    with pytest.raises(ValidationError, match="component_type\n  unexpected value"):
        EdxBookmarkBaseEventField(**invalid_subfield)


@pytest.mark.parametrize(
    "component_usage_id",
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
        (
            "block-v1:orgX=CS111=20_T1+type@sequential1"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
@custom_given(EdxBookmarkBaseEventField)
def test_fields_edx_edx_bookmark_base_event_field_with_invalid_component_usage_id_value(
    component_usage_id, field
):
    """Test that an invalid `EdxBookmarkBaseEventField` raises a `ValidationError`."""

    invalid_field = json.loads(field.json())
    invalid_field["component_usage_id"] = component_usage_id

    with pytest.raises(ValidationError, match="id\n  string does not match regex"):
        EdxBookmarkBaseEventField(**invalid_field)


@custom_given(EdxBookmarkAddedEventField)
def test_models_edx_edx_bookmark_added_event_field_with_valid_values(field):
    """Test that a valid `EdxBookmarkAddedEventField` does not raise a
    `ValidationError`.
    """

    assert re.match(
        r"^$|^course-v1:.+\+.+\+.+$",
        field.course_id,
    )


@pytest.mark.parametrize(
    "course_id",
    [
        "course-v1:+course+not_empty",
        "course-v1:org",
        "course-v1:org+course",
        "course-v1:org+course+",
    ],
)
@custom_given(EdxBookmarkAddedEventField)
def test_models_edx_edx_bookmark_added_event_field_with_invalid_course_id_value(
    course_id, statement
):
    """Test that an invalid `EdxBookmarkAddedEventField` statement raises a
    `ValidationError`.
    """
    invalid_statement = json.loads(statement.json())
    invalid_statement["course_id"] = course_id

    with pytest.raises(
        ValidationError, match="course_id\n  string does not match regex"
    ):
        EdxBookmarkAddedEventField(**invalid_statement)


@custom_given(EdxBookmarkListedEventField)
def test_models_edx_edx_bookmark_listed_event_field_with_valid_values(field):
    """Test that a valid `EdxBookmarkListedEventField` does not raise a
    `ValidationError`.
    """

    if field.course_id is not None:
        assert re.match(
            r"^$|^course-v1:.+\+.+\+.+$",
            field.course_id,
        )
    assert field.list_type in ("per_course", "all_courses")


@pytest.mark.parametrize(
    "list_type",
    ["percourse", "per_courses", "allcourses", "all_course"],
)
@custom_given(EdxBookmarkListedEventField)
def test_models_edx_edx_bookmark_listed_event_field_with_invalid_list_type_value(
    list_type, subfield
):
    """Test that an invalid `list_type` value in `EdxBookmarkListedEventField` raises a
    `ValidationError`.
    """
    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["list_type"] = list_type

    with pytest.raises(ValidationError, match="list_type\n  unexpected value"):
        EdxBookmarkListedEventField(**invalid_subfield)


@pytest.mark.parametrize(
    "course_id",
    [
        "course-v1:+course+not_empty",
        "course-v1:org",
        "course-v1:org+course",
        "course-v1:org+course+",
    ],
)
@custom_given(EdxBookmarkListedEventField)
def test_models_edx_edx_bookmark_listed_event_field_with_invalid_course_id_value(
    course_id, statement
):
    """Test that an invalid `EdxBookmarkListedEventField` statement raises a
    `ValidationError`.
    """
    invalid_statement = json.loads(statement.json())
    invalid_statement["course_id"] = course_id

    with pytest.raises(
        ValidationError, match="course_id\n  string does not match regex"
    ):
        EdxBookmarkListedEventField(**invalid_statement)


@custom_given(EdxBookmarkRemovedEventField)
def test_models_edx_edx_bookmark_removed_event_field_with_valid_values(field):
    """Test that a valid `EdxBookmarkRemovedEventField` does not raise a
    `ValidationError`.
    """

    assert re.match(
        r"^$|^course-v1:.+\+.+\+.+$",
        field.course_id,
    )


@pytest.mark.parametrize(
    "course_id",
    [
        "course-v1:+course+not_empty",
        "course-v1:org",
        "course-v1:org+course",
        "course-v1:org+course+",
    ],
)
@custom_given(EdxBookmarkRemovedEventField)
def test_models_edx_edx_bookmark_removed_event_field_with_invalid_course_id_value(
    course_id, statement
):
    """Test that an invalid `EdxBookmarkRemovedEventField` statement raises a
    `ValidationError`.
    """
    invalid_statement = json.loads(statement.json())
    invalid_statement["course_id"] = course_id

    with pytest.raises(
        ValidationError, match="course_id\n  string does not match regex"
    ):
        EdxBookmarkRemovedEventField(**invalid_statement)


@custom_given(UIEdxCourseToolAccessedEventField)
def test_models_edx_ui_edx_course_tool_accessed_event_field_with_valid_values(field):
    """Test that a valid `UIEdxCourseToolAccessedEventField` does not raise a
    `ValidationError`.
    """

    assert field.tool_name in ("edx.bookmarks", "edx.reviews", "edx.updates")


@pytest.mark.parametrize(
    "tool_name",
    [
        "edxbookmarks",
        "edx.bookmark",
        "edxreviews",
        "edx.review",
        "edxupdates",
        "edx.update",
    ],
)
@custom_given(UIEdxCourseToolAccessedEventField)
def test_models_edx_ui_edx_course_tool_accessed_event_field_with_invalid_tool_name_value(  # noqa: E501
    tool_name, subfield
):
    """Test that an invalid `tool_name` value in `EdxBookmarkListedEventField` raises a
    `ValidationError`.
    """
    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["tool_name"] = tool_name

    with pytest.raises(ValidationError, match="tool_name\n  unexpected value"):
        UIEdxCourseToolAccessedEventField(**invalid_subfield)
