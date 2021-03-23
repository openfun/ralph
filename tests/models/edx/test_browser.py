"""Tests for the browser event models"""

import pytest
from pydantic.error_wrappers import ValidationError

from tests.fixtures.edx.browser import BaseBrowserEventFactory


@pytest.mark.parametrize(
    "kwargs",
    [
        {"session": ""},
        {"session": "cc7ee04f8e4eb7e84f8c4c441cc78f40"},
        {"page": "https://www.fun-mooc.fr/"},
        {"page": "/this/is/a/valid/relative/url"},
        {"page": "/"},
    ],
)
def test_models_edx_browser_base_browser_event_with_valid_content(kwargs):
    """Tests that a valid base browser event does not raise a ValidationError."""

    try:
        BaseBrowserEventFactory(**kwargs)
    except ValidationError:
        pytest.fail(
            f"Valid base browser event with {kwargs} should not raise exceptions"
        )


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"event_source": "not_browser"}, "unexpected value; permitted: 'browser'"),
        ({"session": "less_than_32_characters"}, "string does not match regex"),
        (
            {"session": "session_more_than_32_character_long"},
            "string does not match regex",
        ),
        ({"session": None}, "not an allowed value"),
        ({"page": None}, "not an allowed value"),
    ],
)
def test_models_edx_browser_base_browser_event_with_invalid_content(kwargs, error):
    """Tests that an invalid base browser event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        BaseBrowserEventFactory(**kwargs)
