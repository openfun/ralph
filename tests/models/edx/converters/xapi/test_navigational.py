"""Tests for the server event xAPI converter"""

import json
from uuid import UUID, uuid5

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.converter import convert_dict_event
from ralph.models.edx.base import BaseContextField
from ralph.models.edx.converters.xapi.navigational import UIPageCloseToPageTerminated
from ralph.models.edx.navigational.statements import UIPageClose


@settings(max_examples=1)
@given(
    st.builds(
        UIPageClose,
        referer=provisional.urls(),
        page=provisional.urls(),
        context=st.builds(
            BaseContextField, user_id=st.just("1"), path=st.just("https://fun-mooc.fr/")
        ),
    ),
    provisional.urls(),
)
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_navigational_ui_page_close_to_page_terminated(
    uuid_namespace, event, platform_url
):
    """Tests that ServerEventToPageViewed.convert returns a JSON string with a constant UUID."""

    event_str = event.json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, UIPageCloseToPageTerminated(uuid_namespace, platform_url)
    )
    xapi_event_dict = json.loads(xapi_event.json(exclude_none=True, by_alias=True))
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": platform_url, "name": "1"},
        },
        "object": {
            "definition": {
                "name": {"en": "page"},
                "type": "http://activitystrea.ms/schema/1.0/page",
            },
            "id": event["page"],
        },
        "timestamp": event["time"],
        "verb": {
            "display": {"en": "terminated"},
            "id": "http://adlnet.gov/expapi/verbs/terminated",
        },
    }
