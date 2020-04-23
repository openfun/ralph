"""
Tests for the event fixture
"""
import json
import urllib.parse

import pandas as pd

from .fixtures.logs import EVENT_TYPES


def test_event_should_return_a_data_frame(event):
    """check that the fixture returns a DataFrame of needed length"""
    for event_type in EVENT_TYPES:
        events = event(10, event_type)
        assert isinstance(events, pd.DataFrame)
        assert isinstance(events.iloc[0], pd.Series)
        assert isinstance(events.iloc[0]["context"], dict)
        assert len(events) == 10


def test_server_event_should_update_values_for_each_line(event):
    """check that the fixture dont have 2 identical usernames"""
    for event_type in EVENT_TYPES:
        events = event(2, event_type)
        assert events.iloc[0]["username"] != events.iloc[1]["username"]
        assert (
            events.iloc[0]["context"]["org_id"] != events.iloc[1]["context"]["org_id"]
        )


def test_event_should_not_contain_sub_type(event):
    """check that the fixture dont contain the sub_type parameter"""
    for event_type in EVENT_TYPES:
        events = event(1, event_type)
        assert "sub_type" not in events.columns


def test_server_event_event_type_field_should_be_equal_to_context_path_field(event):
    """check that the server event "event_type" is equal to
    context[path]
    """
    events = event(1, "server")
    assert events.iloc[0]["event_type"] == events.iloc[0]["context"]["path"]


def test_browser_event_path_and_name_field(event):
    """check that the event path is /event and the name is equal to the
    event_type
    """
    events = event(1, "browser")
    assert events.iloc[0]["context"]["path"] == "/event"
    assert events.iloc[0]["name"] == events.iloc[0]["event_type"]


def test_browser_event_of_sub_type_problem_show(event):
    """check the problem_show browser event"""
    events = event(1, "browser", "problem_show")
    assert isinstance(events.iloc[0]["event"], str)
    parsed_json = json.loads(events.iloc[0]["event"])
    assert "problem" in parsed_json


def test_browser_event_of_sub_type_problem_check(event):
    """"check the problem_check browser event"""
    events = event(1, "browser", "problem_check")
    assert isinstance(events.iloc[0]["event"], str)
    assert len(urllib.parse.parse_qs(events.iloc[0]["event"])) >= 1 or (
        events.iloc[0]["event"] == ""
    )


def test_browser_event_of_sub_type_problem_graded(event):
    """"check the problem_graded browser event"""
    events = event(1, "browser", "problem_graded")
    assert isinstance(events.iloc[0]["event"], list)
    assert len(events.iloc[0]["event"]) == 2
    assert len(urllib.parse.parse_qs(events.iloc[0]["event"][0])) >= 1 or (
        events.iloc[0]["event"][0] == ""
    )
