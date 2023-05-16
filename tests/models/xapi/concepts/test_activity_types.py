"""Tests for the xAPI activity types concepts."""
import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st

from ralph.models.xapi.concepts.activity_types.acrossx_profile import MessageActivity
from ralph.models.xapi.concepts.activity_types.activity_streams_vocabulary import (
    PageActivity,
)
from ralph.models.xapi.concepts.activity_types.scorm_profile import (
    CMIInteractionActivity,
    CourseActivity,
    ModuleActivity,
    ProfileActivity,
)
from ralph.models.xapi.concepts.activity_types.video import VideoActivity
from ralph.models.xapi.concepts.activity_types.virtual_classroom import (
    VirtualClassroomActivity,
)

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@settings(deadline=None)
@pytest.mark.parametrize(
    "class_, definition_type",
    [
        (MessageActivity, "https://w3id.org/xapi/acrossx/activities/message"),
        (PageActivity, "http://activitystrea.ms/schema/1.0/page"),
        (CMIInteractionActivity, "http://adlnet.gov/expapi/activities/cmi.interaction"),
        (CourseActivity, "http://adlnet.gov/expapi/activities/course"),
        (ModuleActivity, "http://adlnet.gov/expapi/activities/module"),
        (ProfileActivity, "http://adlnet.gov/expapi/activities/profile"),
        (VideoActivity, "https://w3id.org/xapi/video/activity-type/video"),
        (
            VirtualClassroomActivity,
            "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom",
        ),
    ],
)
@custom_given(st.data())
def test_models_xapi_concept_activity_types_with_valid_field(
    class_, definition_type, data
):
    """Tests that a valid xAPI activity has the expected the `definition`.`type`
    value.
    """
    field = json.loads(data.draw(custom_builds(class_)).json())
    assert field["definition"]["type"] == definition_type
