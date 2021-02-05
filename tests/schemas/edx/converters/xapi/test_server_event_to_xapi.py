"""Tests for the server event xAPI converter"""

import json

import pytest

from ralph.schemas.edx.converters.xapi.server_event_to_xapi import ServerEventToXapi

from tests.fixtures.logs import EventType

PLATFORM = "https://www.fun-mooc.fr"
CONVERTER = ServerEventToXapi(PLATFORM)


def test_converting_invalid_server_event_should_return_none(event):
    """The converter should return None for invalid events"""

    server_event = event(EventType.SERVER)
    server_event["username"] = "This user name is more than 32 chars long!"
    assert CONVERTER.convert(server_event) is None


@pytest.mark.parametrize("user_id", [None, "", 123])
@pytest.mark.parametrize("course_user_tags", [None, {}, {"some_key": "some_value"}])
def test_server_xapi_converter_returns_actor_timestamp_and_context(
    event, user_id, course_user_tags
):
    """Test that ServerEventToXapi returns actor, timestamp and context"""

    # Generate event
    context_args = {
        "user_id": user_id,
        "course_user_tags": {} if course_user_tags is None else course_user_tags,
    }
    server_event = event(EventType.SERVER, context_args=context_args)

    # Remove course_user_tags when it's set to None
    expected_course_user_tags = {
        "https://www.edx.org/extension/course_user_tags": course_user_tags,
    }
    if course_user_tags is None:
        del server_event["context"]["course_user_tags"]
        expected_course_user_tags = {}
    if not course_user_tags:
        expected_course_user_tags = {}

    # Convert event to xAPI
    xapi_event = json.loads(CONVERTER.convert(server_event))
    user_id = str(user_id) if user_id else "student"
    assert xapi_event["actor"]["objectType"] == "Agent"
    assert xapi_event["actor"]["account"]["name"] == user_id
    assert xapi_event["actor"]["account"]["homePage"] == PLATFORM
    assert xapi_event["timestamp"] == server_event["time"]
    assert xapi_event["context"] == {
        "extensions": {
            "https://www.edx.org/extension/accept_language": server_event[
                "accept_language"
            ],
            "https://www.edx.org/extension/agent": server_event["agent"],
            "https://www.edx.org/extension/course_id": server_event["context"][
                "course_id"
            ],
            **expected_course_user_tags,
            "https://www.edx.org/extension/host": server_event["host"],
            "https://www.edx.org/extension/ip": server_event["ip"],
            "https://www.edx.org/extension/org_id": server_event["context"]["org_id"],
            "https://www.edx.org/extension/path": server_event["context"]["path"],
            "https://www.edx.org/extension/request": server_event["event"],
        },
        "platform": PLATFORM,
    }
