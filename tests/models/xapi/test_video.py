"""Tests for the xAPI played statement"""

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.xapi.fields.actors import ActorAccountField, ActorField
from ralph.models.xapi.video.events import VideoPlayed
from ralph.models.xapi.video.fields.contexts import VideoPlayedContextField
from ralph.models.xapi.video.fields.objects import (
    VideoObjectDefinitionField,
    VideoObjectField,
)
from ralph.models.xapi.video.fields.results import VideoPlayedResultField
from ralph.models.xapi.video.fields.verbs import VideoPlayedVerbField


@settings(max_examples=1)
@given(
    st.builds(
        VideoPlayed,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definitions=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoPlayedVerbField),
        context=st.builds(VideoPlayedContextField),
        result=st.builds(VideoPlayedResultField),
    )
)
def test_models_xapi_video_played_statement(statement):
    """Tests that a video played statement has the expected verb.id and object.definition."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/played"
