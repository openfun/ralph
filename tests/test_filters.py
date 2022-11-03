"""Tests for the ralph.filters module."""

import pytest

from ralph import filters
from ralph.exceptions import EventKeyError


def test_filters_anonymous_with_empty_events():
    """Tests the anonymous filter when input dict has not the expected `username`
    key.
    """

    event = {}
    with pytest.raises(EventKeyError):
        filters.anonymous(event)


def test_filters_anonymous_filtering():
    """Tests anonymous filtering reliability."""

    event = {"username": "john"}
    anonymous_event = {"username": ""}
    assert filters.anonymous(event) == event
    assert filters.anonymous(anonymous_event) is None
