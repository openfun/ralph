"""Tests for the problem interaction xAPI converters"""

import json
from uuid import UUID, uuid5

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.converter import convert_dict_event
from ralph.models.edx.converters.xapi.problem import (
    DemandhintDisplayedToInteractionInteracted,
    ShowanswerToInteractionAsked,
)
from ralph.models.edx.problem import (
    DemandhintDisplayed,
    DemandhintDisplayedEventField,
    Showanswer,
)
from ralph.models.edx.x_block import ContextField, ContextModuleField


@settings(max_examples=1)
@given(
    st.builds(
        DemandhintDisplayed,
        referer=provisional.urls(),
        context=st.builds(
            ContextField,
            user_id=st.just("1"),
            path=st.just("https://fun-mooc.fr/"),
            module=st.builds(ContextModuleField),
        ),
        event=st.builds(DemandhintDisplayedEventField, hint_text=st.just("Hint text")),
    ),
    provisional.urls(),
)
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_demandhint_displayed_to_interaction_interacted_conversion(
    uuid_namespace, event, home_page
):
    """Tests that converting with `DemandhintDisplayedToInteractionInteracted`
    returns the expected value.
    """

    event_str = event.json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event,
        event_str,
        DemandhintDisplayedToInteractionInteracted(uuid_namespace, home_page),
    )
    xapi_event_dict = json.loads(xapi_event.json(exclude_none=True, by_alias=True))
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": home_page, "name": "1"},
        },
        "object": {
            "definition": {
                "name": {"en-US": "interaction"},
                "type": "http://adlnet.gov/expapi/activities/interaction",
                "extensions": {
                    "https://w3id.org/xapi/acrossx/extensions/supplemental-info": event[
                        "event"
                    ]["hint_index"],
                    "https://w3id.org/xapi/acrossx/extensions/total-items": event[
                        "event"
                    ]["hint_len"],
                },
            },
            "id": home_page + "/" + event["context"]["module"]["usage_key"],
        },
        "result": {"response": event["event"]["hint_text"]},
        "timestamp": event["time"],
        "verb": {
            "display": {"en-US": "interacted"},
            "id": "http://adlnet.gov/expapi/verbs/interacted",
        },
    }


@settings(max_examples=1)
@given(
    st.builds(
        Showanswer,
        referer=provisional.urls(),
        context=st.builds(
            ContextField,
            user_id=st.just("1"),
            path=st.just("https://fun-mooc.fr/"),
            module=st.builds(ContextModuleField),
        ),
    ),
    provisional.urls(),
)
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_showanswer_to_interaction_asked_conversion(uuid_namespace, event, home_page):
    """Tests that converting with `ShowanswerToInteractionAsked` returns the expected value."""

    event_str = event.json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event,
        event_str,
        ShowanswerToInteractionAsked(uuid_namespace, home_page),
    )
    xapi_event_dict = json.loads(xapi_event.json(exclude_none=True, by_alias=True))
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": home_page, "name": "1"},
        },
        "object": {
            "definition": {
                "name": {"en-US": "interaction"},
                "type": "http://adlnet.gov/expapi/activities/interaction",
            },
            "id": home_page + "/" + event["context"]["module"]["usage_key"],
        },
        "timestamp": event["time"],
        "verb": {
            "display": {"en-US": "asked"},
            "id": "http://adlnet.gov/expapi/verbs/asked",
        },
    }
