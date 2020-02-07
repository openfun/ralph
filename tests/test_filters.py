"""
Tests for the ralph.filters module
"""
import pandas as pd
import pytest

from ralph import filters
from ralph.exceptions import EventKeyError


def test_anonymous_with_empty_events():
    """Test the anonymous filter when input DataFrame has not the expected
    'username' key.
    """

    events = pd.DataFrame()
    with pytest.raises(EventKeyError):
        filters.anonymous(events)


def test_anonymous_filtering():
    """Test anonymous filtering reliability."""

    events = pd.DataFrame({"username": ["john", ""]})
    assert len(events) == 2
    assert len(filters.anonymous(events)) == 1
    assert filters.anonymous(events).equals(pd.DataFrame({"username": ["john"]}))
