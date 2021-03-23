"""Tests for the navigational event models"""

import pytest
from pydantic.error_wrappers import ValidationError

from tests.fixtures.edx.navigational import (
    PageCloseBrowserEventFactory,
    SeqGotoBrowserEventFactory,
    SeqNextBrowserEventFactory,
    SeqPrevBrowserEventFactory,
)


def test_models_edx_browser_page_close_browser_event_with_valid_content():
    """Tests that a valid page_close browser event does not raise a ValidationError."""

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
    """Tests that an invalid page_close browser event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        PageCloseBrowserEventFactory(**kwargs)


def test_models_edx_browser_seq_goto_browser_event_with_valid_content():
    """Tests that a valid seq_goto browser event does not raise a ValidationError."""

    try:
        SeqGotoBrowserEventFactory()
    except ValidationError:
        pytest.fail("Valid seq_goto browser event should not raise exceptions")


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"name": None}, "name\n  none is not an allowed value"),
        ({"name": "goto"}, "unexpected value; permitted: 'seq_goto'"),
        ({"event_type": None}, "event_type\n  none is not an allowed value"),
        ({"event_type": "goto"}, "unexpected value; permitted: 'seq_goto'"),
        ({"event": None}, "event\n  none is not an allowed value"),
        (
            {"event": "NavigationalBrowserEventEventFieldFactory"},
            "event\n  value is not a valid dict",
        ),
    ],
)
def test_models_edx_browser_seq_goto_browser_event_with_invalid_content(kwargs, error):
    """Tests that an invalid page_close browser event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        SeqGotoBrowserEventFactory(**kwargs)


def test_models_edx_browser_seq_next_browser_event_with_valid_content():
    """Tests that a valid seq_next browser event does not raise a ValidationError."""

    try:
        SeqNextBrowserEventFactory()
    except ValidationError:
        pytest.fail("Valid seq_next browser event should not raise exceptions")


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"name": None}, "name\n  none is not an allowed value"),
        ({"name": "next"}, "unexpected value; permitted: 'seq_next'"),
        ({"event_type": None}, "event_type\n  none is not an allowed value"),
        ({"event_type": "next"}, "unexpected value; permitted: 'seq_next'"),
        ({"event": None}, "event\n  none is not an allowed value"),
        (
            {"event__old": 0, "event__new": 10},
            "event\n  event.new - event.old should be equal to 1",
        ),
        (
            {"event": "NavigationalBrowserEventEventFieldFactory"},
            "event\n  value is not a valid dict",
        ),
    ],
)
def test_models_edx_browser_seq_next_browser_event_with_invalid_content(kwargs, error):
    """Tests that an invalid seq_next browser event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        SeqNextBrowserEventFactory(**kwargs)


def test_models_edx_browser_seq_prev_browser_event_with_valid_content():
    """Tests that a valid seq_prev browser event does not raise a ValidationError."""

    try:
        SeqPrevBrowserEventFactory()
    except ValidationError:
        pytest.fail("Valid seq_prev browser event should not raise exceptions")


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"name": None}, "name\n  none is not an allowed value"),
        ({"name": "prev"}, "unexpected value; permitted: 'seq_prev'"),
        ({"event_type": None}, "event_type\n  none is not an allowed value"),
        ({"event_type": "prev"}, "unexpected value; permitted: 'seq_prev'"),
        ({"event": None}, "event\n  none is not an allowed value"),
        (
            {"event__old": 0, "event__new": 10},
            "event\n  event.old - event.new should be equal to 1",
        ),
        (
            {"event": "NavigationalBrowserEventEventFieldFactory"},
            "event\n  value is not a valid dict",
        ),
    ],
)
def test_models_edx_browser_seq_prev_browser_event_with_invalid_content(kwargs, error):
    """Tests that an invalid seq_prev browser event raises a ValidationError."""

    with pytest.raises(ValidationError, match=error):
        SeqPrevBrowserEventFactory(**kwargs)
