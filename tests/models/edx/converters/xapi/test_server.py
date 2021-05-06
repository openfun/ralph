"""Tests for the server event xAPI converter"""

import json

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models import converter as converter_module
from ralph.models.edx.converters.xapi.server import ServerEventToXapi
from ralph.models.edx.server import ServerEvent, ServerEventField


@pytest.fixture(autouse=True)
def setup_edx_uuid_namespace(monkeypatch):
    """Monkeypatches the required EDX_UUID_NAMESPACE configuration."""

    uuid = "51f5c14e-0150-4766-88d2-6f7991ad6bfe"
    monkeypatch.setattr(converter_module, "EDX_UUID_NAMESPACE", uuid)


@settings(max_examples=1)
@given(
    st.builds(
        ServerEvent, event=st.builds(ServerEventField), referer=provisional.urls()
    )
)
def test_models_edx_converters_xapi_server_server_event_to_xapi_convert_constant_uuid(
    event,
):
    """Tests that ServerEventToXapi.convert returns a JSON string with a constant UUID."""

    home_page = "https://www.fun-mooc.fr"
    event_str = event.json()
    event = json.loads(event_str)
    xapi_event1 = json.loads(ServerEventToXapi(home_page).convert(event, event_str))
    xapi_event2 = json.loads(ServerEventToXapi(home_page).convert(event, event_str))
    assert xapi_event1["id"] == xapi_event2["id"]


@settings(max_examples=1)
@given(
    st.builds(
        ServerEvent,
        event=st.builds(ServerEventField),
        host=st.just("1"),
        referer=provisional.urls(),
    ),
    st.builds(
        ServerEvent,
        event=st.builds(ServerEventField),
        host=st.just("2"),
        referer=provisional.urls(),
    ),
)
def test_models_edx_converters_xapi_server_server_event_to_xapi_convert_unique_uuid(
    event1, event2
):
    """Tests that ServerEventToXapi.convert returns a JSON string with a unique UUID."""

    home_page = "https://www.fun-mooc.fr"
    event_str1 = event1.json()
    event_str2 = event2.json()
    event1 = json.loads(event_str1)
    event2 = json.loads(event_str2)
    xapi_event1 = json.loads(ServerEventToXapi(home_page).convert(event1, event_str1))
    xapi_event2 = json.loads(ServerEventToXapi(home_page).convert(event2, event_str2))
    assert xapi_event1["id"] != xapi_event2["id"]


@settings(max_examples=1)
@given(
    st.builds(
        ServerEvent, event=st.builds(ServerEventField), referer=provisional.urls()
    )
)
def test_models_edx_converters_xapi_server_server_event_to_xapi_convert_with_valid_event(
    event,
):
    """Tests that ServerEventToXapi.convert returns the expected converter xAPI statement."""

    home_page = "https://www.fun-mooc.fr"
    event_str = event.json()
    event = json.loads(event_str)
    event["context"]["user_id"] = "1"
    event["event_type"] = "/main/blog"
    event["context"]["path"] = "/main/blog"
    xapi_event = json.loads(ServerEventToXapi(home_page).convert(event, event_str))
    extensions = {
        "https://www.edx.org/extension/accept_language": event["accept_language"],
        "https://www.edx.org/extension/agent": event["agent"],
        "https://www.edx.org/extension/course_id": event["context"]["course_id"],
        "https://www.edx.org/extension/host": event["host"],
        "https://www.edx.org/extension/ip": event["ip"],
        "https://www.edx.org/extension/org_id": event["context"]["org_id"],
        "https://www.edx.org/extension/course_user_tags": event["context"][
            "course_user_tags"
        ],
        "https://www.edx.org/extension/path": event["context"]["path"],
    }
    # extensions that are empty or non are removed from the xAPI statement
    for key in list(extensions.keys()):
        if not extensions[key]:
            del extensions[key]

    del xapi_event["id"]
    assert xapi_event == {
        "actor": {
            "account": {"homePage": "https://www.fun-mooc.fr", "name": "1"},
        },
        "context": {
            "extensions": extensions,
        },
        "object": {
            "definition": {
                "name": {"en": "page"},
                "type": "http://activitystrea.ms/schema/1.0/page",
            },
            "id": "https://www.fun-mooc.fr/main/blog",
        },
        "timestamp": event["time"],
        "verb": {
            "display": {"en": "viewed"},
            "id": "http://id.tincanapi.com/verb/viewed",
        },
    }


@settings(max_examples=1)
@given(
    st.builds(
        ServerEvent, event=st.builds(ServerEventField), referer=provisional.urls()
    )
)
def test_models_edx_converters_xapi_server_server_event_to_xapi_convert_with_anonymous_user(
    event,
):
    """Tests that ServerEventToXapi.convert replaces anonymous usernames with with `anonymous`."""

    event_str = event.json()
    event = json.loads(event_str)
    event["context"]["user_id"] = ""
    xapi_event = json.loads(
        ServerEventToXapi("https://www.fun-mooc.fr").convert(event, event_str)
    )
    assert xapi_event["actor"]["account"]["name"] == "anonymous"
