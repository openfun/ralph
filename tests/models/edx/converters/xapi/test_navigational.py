"""Tests for the server event xAPI converter"""

import json
from uuid import UUID, uuid5

import pytest
from hypothesis import provisional

from ralph.models.converter import convert_dict_event
from ralph.models.edx.converters.xapi.navigational import UIPageCloseToPageTerminated
from ralph.models.edx.navigational.statements import UIPageClose

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(UIPageClose, provisional.urls())
@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_navigational_ui_page_close_to_page_terminated(
    uuid_namespace, event, platform_url
):
    """Tests that ServerEventToPageViewed.convert returns a JSON string with a
    constant UUID.
    """

    event.context.course_id = ""
    event.context.org_id = ""
    event.context.user_id = "1"
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
                "name": {"en-US": "page"},
                "type": "http://activitystrea.ms/schema/1.0/page",
            },
            "id": event["page"],
        },
        "timestamp": event["time"],
        "verb": {
            "display": {"en-US": "terminated"},
            "id": "http://adlnet.gov/expapi/verbs/terminated",
        },
    }
