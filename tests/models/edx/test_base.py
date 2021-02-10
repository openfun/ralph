"""Tests for the base event model"""

import pytest
from pydantic.error_wrappers import ValidationError

from tests.fixtures.edx.server import BaseEventFactory


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ip": "51.255.9.27"},
        {"ip": "8.8.8.8"},
        {"ip": ""},
        {"event_source": "server"},
        {"agent": ""},
        {"host": ""},
        {"referer": ""},
        {"referer": "https://www.fun-mooc.fr/"},
        {"referer": "https://www.fun-mooc.fr/event?event_type=page_close"},
        {"context__user_id": ""},
        {"context__user_id": None},
        {"context__user_id": 213456},
        {"context__org_id": "", "context__course_id": ""},
        {"context__org_id": "org", "context__course_id": "course-v1:org+any+any"},
    ],
)
def test_models_edx_base_event_with_valid_content(kwargs):
    """Test that a valid base event does not raise a ValidationError."""

    try:
        BaseEventFactory(**kwargs)
    except ValidationError:
        pytest.fail(f"Valid base event with {kwargs} should not raise exceptions")


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"ip": "invalid_ip"}, "not a valid IPv4 address"),
        ({"ip": "  "}, "not a valid IPv4 address"),
        ({"event_source": "not_server"}, "unexpected value; permitted: 'server'"),
        ({"page": "not_None"}, "unexpected value; permitted: None"),
        ({"page": 0}, "unexpected value; permitted: None"),
        ({"page": ""}, "unexpected value; permitted: None"),
        ({"page": {}}, "unhashable type: 'dict'"),
        ({"referer": 1}, "invalid or missing URL scheme"),
        ({"referer": "this/is/not/a/valid/url"}, "invalid or missing URL scheme"),
        ({"context__user_id": "invalid"}, "value is not a valid integer"),
        ({"context__user_id": {}}, "value is not a valid integer"),
        ({"context__org_id": None}, "org_id\n  none is not an allowed value"),
        ({"context__org_id": {}}, "org_id\n  str type expected"),
        ({"context__course_id": "+org+any"}, "course_id must match regex"),
        (
            {"context__course_id": "course-v1:+course+not_empty"},
            "course_id must match regex",
        ),
        (
            {"context__course_id": "course-v1:NOT_org+course+session"},
            "course_id must match regex",
        ),
        (
            {"context__org_id": "org", "context__course_id": ""},
            "course_id must match regex",
        ),
        (
            {"context__org_id": "org", "context__course_id": "course-v1:org"},
            "course_id must match regex",
        ),
        (
            {"context__org_id": "org", "context__course_id": "course-v1:org+course"},
            "course_id must match regex",
        ),
        (
            {"context__org_id": "org", "context__course_id": "course-v1:org+course+"},
            "course_id must match regex",
        ),
    ],
)
def test_models_edx_base_event_with_invalid_content(kwargs, error):
    """Test that an invalid base event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        BaseEventFactory(**kwargs)
