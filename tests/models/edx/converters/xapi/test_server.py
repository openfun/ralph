"""Tests for the server event xAPI converter."""

import json
from uuid import UUID, uuid5

import pytest
from hypothesis import provisional, settings

from ralph.models.converter import convert_dict_event, convert_str_event
from ralph.models.edx.converters.xapi.server import ServerEventToPageViewed
from ralph.models.edx.server import Server

from tests.fixtures.hypothesis_ strategies import custom_given
from tests.factories import mock_instance, mock_url

@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_server_server_event_to_page_viewed_constant_uuid(
    uuid_namespace
):
    """Test that `ServerEventToPageViewed.convert` returns a JSON string with a
    constant UUID.
    """
    event = mock_instance(Server)
    platform_url = mock_url()

    event_str = event.json()
    event = json.loads(event_str)
    xapi_event1 = convert_str_event(
        event_str, ServerEventToPageViewed(uuid_namespace, platform_url)
    )
    xapi_event2 = convert_dict_event(
        event, event_str, ServerEventToPageViewed(uuid_namespace, platform_url)
    )
    assert xapi_event1.id == xapi_event2.id


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_server_server_event_to_page_viewed(
    uuid_namespace
):
    """Test that converting with `ServerEventToPageViewed` returns the expected xAPI
    statement.
    """
    event = mock_instance(Server)
    platform_url = mock_url()

    event.event_type = "/main/blog"
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
                "type": "http://activitystrea.ms/schema/1.0/page",
            },
            "id": platform_url + "/main/blog",
        },
        "timestamp": event["time"],
        "verb": {
            "id": "http://id.tincanapi.com/verb/viewed",
        },
        "version": "1.0.0",
    }


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_server_server_event_to_page_viewed_with_anonymous_user(  # noqa: E501
    uuid_namespace, event
):
    """Test that anonymous usernames are replaced with `anonymous`."""
    platform_url = mock_url()

    event.context.user_id = ""
    event_str = event.json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, ServerEventToPageViewed(uuid_namespace, platform_url)
    )
    assert xapi_event.actor.account.name == "anonymous"
