"""Tests for the browser event models"""

import pytest
from pydantic.error_wrappers import ValidationError

from tests.fixtures.edx.browser import (
    BaseBrowserEventFactory,
    PageCloseBrowserEventFactory,
)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"event_source": "browser"},
        {"session": ""},
        {"session": "cc7ee04f8e4eb7e84f8c4c441cc78f40"},
        {"page": "https://www.fun-mooc.fr/"},
        {"page": "/this/is/a/valid/relative/url"},
        {"page": "/"},
    ],
)
def test_models_edx_browser_base_browser_event_with_valid_content(kwargs):
    """Test that a valid base browser event does not raise a ValidationError."""

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
    """Test that an invalid base browser event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        BaseBrowserEventFactory(**kwargs)


def test_models_edx_browser_page_close_browser_event_with_valid_content():
    """Test that a valid page_close browser event does not raise a ValidationError."""

    try:
        PageCloseBrowserEventFactory()
    except ValidationError:
        pytest.fail("Valid page_close browser event should not raise exceptions")


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"name": "close"}, "unexpected value; permitted: 'page_close'"),
        ({"event_type": "close"}, "unexpected value; permitted: 'page_close'"),
        ({"event": ""}, "unexpected value; permitted: '{}'"),
    ],
)
def test_models_edx_browser_page_close_browser_event_with_invalid_content(
    kwargs, error
):
    """Test that an invalid page_close browser event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        PageCloseBrowserEventFactory(**kwargs)
