"""Tests for the xAPI verbs concepts."""
import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st

from ralph.models.xapi.concepts.verbs.acrossx_profile import PostedVerb
from ralph.models.xapi.concepts.verbs.activity_streams_vocabulary import (
    JoinVerb,
    LeaveVerb,
)
from ralph.models.xapi.concepts.verbs.adl_vocabulary import AnsweredVerb, AskedVerb
from ralph.models.xapi.concepts.verbs.scorm_profile import (
    CompletedVerb,
    InitializedVerb,
    InteractedVerb,
    TerminatedVerb,
)
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import (
    DownloadedVerb,
    ViewedVerb,
)
from ralph.models.xapi.concepts.verbs.video import PausedVerb, PlayedVerb, SeekedVerb
from ralph.models.xapi.concepts.verbs.virtual_classroom import (
    LoweredHandVerb,
    MutedVerb,
    RaisedHandVerb,
    SharedScreenVerb,
    StartedCameraVerb,
    StoppedCameraVerb,
    UnmutedVerb,
    UnsharedScreenVerb,
)

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@settings(deadline=None)
@pytest.mark.parametrize(
    "class_, verb_id",
    [
        (PostedVerb, "https://w3id.org/xapi/acrossx/verbs/posted"),
        (JoinVerb, "http://activitystrea.ms/join"),
        (LeaveVerb, "http://activitystrea.ms/leave"),
        (AnsweredVerb, "http://adlnet.gov/expapi/verbs/answered"),
        (AskedVerb, "http://adlnet.gov/expapi/verbs/asked"),
        (CompletedVerb, "http://adlnet.gov/expapi/verbs/completed"),
        (InitializedVerb, "http://adlnet.gov/expapi/verbs/initialized"),
        (InteractedVerb, "http://adlnet.gov/expapi/verbs/interacted"),
        (TerminatedVerb, "http://adlnet.gov/expapi/verbs/terminated"),
        (ViewedVerb, "http://id.tincanapi.com/verb/viewed"),
        (DownloadedVerb, "http://id.tincanapi.com/verb/downloaded"),
        (PausedVerb, "https://w3id.org/xapi/video/verbs/paused"),
        (PlayedVerb, "https://w3id.org/xapi/video/verbs/played"),
        (SeekedVerb, "https://w3id.org/xapi/video/verbs/seeked"),
        (LoweredHandVerb, "https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand"),
        (MutedVerb, "https://w3id.org/xapi/virtual-classroom/verbs/muted"),
        (RaisedHandVerb, "https://w3id.org/xapi/virtual-classroom/verbs/raised-hand"),
        (
            SharedScreenVerb,
            "https://w3id.org/xapi/virtual-classroom/verbs/shared-screen",
        ),
        (
            StartedCameraVerb,
            "https://w3id.org/xapi/virtual-classroom/verbs/started-camera",
        ),
        (
            StoppedCameraVerb,
            "https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera",
        ),
        (UnmutedVerb, "https://w3id.org/xapi/virtual-classroom/verbs/unmuted"),
        (
            UnsharedScreenVerb,
            "https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen",
        ),
    ],
)
@custom_given(st.data())
def test_models_xapi_concept_verbs_with_valid_field(class_, verb_id, data):
    """Tests that a valid xAPI verb has the expected the `id` value."""
    field = json.loads(data.draw(custom_builds(class_)).json())
    assert field["id"] == verb_id
