"""Tests for the server event xAPI converter."""

import json
from uuid import UUID, uuid5

import pytest
from hypothesis import provisional

from ralph.models.converter import convert_dict_event, convert_str_event
from ralph.models.edx.converters.xapi.server import ServerEventToPageViewed
from ralph.models.edx.server import Server

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(Server, provisional.urls())
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_server_server_event_to_xapi_convert_constant_uuid(
    uuid_namespace, event, platform_url
):
    """Tests that `ServerEventToPageViewed.convert` returns a JSON string with a
    constant UUID.
    """
    event_str = event.json()
    event = json.loads(event_str)
    xapi_event1 = convert_str_event(
        event_str, ServerEventToPageViewed(uuid_namespace, platform_url)
    )
    xapi_event2 = convert_dict_event(
        event, event_str, ServerEventToPageViewed(uuid_namespace, platform_url)
    )
    assert xapi_event1.id == xapi_event2.id


# pylint: disable=line-too-long
@custom_given(Server, provisional.urls())
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_server_server_event_to_xapi_convert_with_valid_event(  # noqa
    uuid_namespace, event, platform_url
):
    """Tests that converting with `ServerEventToPageViewed` returns the expected xAPI
    statement.
    """
    event.event_type = "/main/blog"
    event.context.course_id = ""
    event.context.org_id = ""
    event.context.user_id = "1"
    event_str = event.json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, ServerEventToPageViewed(uuid_namespace, platform_url)
    )
    xapi_event_dict = json.loads(xapi_event.json(exclude_none=True, by_alias=True))
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": platform_url, "name": "1"},
        },
        "object": {
            "definition": {
                "name": {"en-US": "page"},
                "type": "http://activitystrea.ms/schema/1.0/page",
            },
            "id": platform_url + "/main/blog",
        },
        "timestamp": event["time"],
        "verb": {
            "display": {"en-US": "viewed"},
            "id": "http://id.tincanapi.com/verb/viewed",
        },
        "version": "1.0.0",
    }


# pylint: disable=line-too-long
@custom_given(Server, provisional.urls())
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_server_server_event_to_xapi_convert_with_anonymous_user(  # noqa
    uuid_namespace, event, platform_url
):
    """Tests that anonymous usernames are replaced with `anonymous`."""

    event.context.user_id = ""
    event_str = event.json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, ServerEventToPageViewed(uuid_namespace, platform_url)
    )
    assert xapi_event.actor.account.name == "anonymous"
