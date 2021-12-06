"""Tests for the open response assessment xAPI converters"""

import json
from uuid import UUID, uuid5

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.converter import convert_dict_event
from ralph.models.edx.base import BaseContextField, ContextModuleField
from ralph.models.edx.converters.xapi.open_response_assessment import (
    ORASaveSubmissionToQuestionSaved,
)
from ralph.models.edx.open_response_assessment.fields.events import (
    ORASaveSubmissionEventField,
    ORASaveSubmissionEventSavedResponseField,
)
from ralph.models.edx.open_response_assessment.statements import ORASaveSubmission


@settings(max_examples=1)
@given(
    st.builds(
        ORASaveSubmission,
        referer=provisional.urls(),
        context=st.builds(
            BaseContextField,
            user_id=st.just("1"),
            path=st.just("https://fun-mooc.fr/"),
            module=st.builds(ContextModuleField, display_name=st.text(min_size=1)),
        ),
        event=st.builds(
            ORASaveSubmissionEventField,
            saved_response=st.builds(
                ORASaveSubmissionEventSavedResponseField,
                parts=st.just([{"text": "first"}, {"text": "second"}]),
            ),
        ),
    ),
    provisional.urls(),
)
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_open_response_assessment_ora_save_submission_to_question_saved_conversion(
    uuid_namespace, event, home_page
):
    """Tests the event conversion `ORASaveSubmissionToQuestionSaved`."""

    event_str = event.json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, ORASaveSubmissionToQuestionSaved(uuid_namespace, home_page)
    )
    xapi_event_dict = json.loads(xapi_event.json(exclude_none=True, by_alias=True))
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": home_page, "name": "1"},
        },
        "object": {
            "definition": {
                "name": {"en-US": event["context"]["module"]["display_name"]},
                "type": "http://adlnet.gov/expapi/activities/question",
            },
            "id": home_page + "/" + event["context"]["module"]["usage_key"],
        },
        "result": {
            "extensions": {
                "http://vocab.xapi.fr/extensions/responses": ["first", "second"]
            }
        },
        "timestamp": event["time"],
        "verb": {
            "display": {"en-US": "saved"},
            "id": "https://w3id.org/xapi/dod-isd/verbs/saved",
        },
    }
