"""Tests for the xAPI played statement"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.selector import ModelSelector
from ralph.models.xapi.fields.actors import ActorAccountField, ActorField
from ralph.models.xapi.video.fields.contexts import (
    VideoCompletedContextField,
    VideoInitializedContextField,
    VideoInteractedContextField,
    VideoPausedContextField,
    VideoPlayedContextField,
    VideoSeekedContextField,
    VideoTerminatedContextField,
)
from ralph.models.xapi.video.fields.objects import (
    VideoObjectDefinitionField,
    VideoObjectField,
)
from ralph.models.xapi.video.fields.results import (
    VideoCompletedResultField,
    VideoInteractedResultField,
    VideoPausedResultField,
    VideoPlayedResultField,
    VideoSeekedResultField,
    VideoTerminatedResultField,
)
from ralph.models.xapi.video.fields.verbs import (
    VideoCompletedVerbField,
    VideoInitializedVerbField,
    VideoInteractedVerbField,
    VideoPausedVerbField,
    VideoPlayedVerbField,
    VideoSeekedVerbField,
    VideoTerminatedVerbField,
)
from ralph.models.xapi.video.statements import (
    VideoCompleted,
    VideoInitialized,
    VideoInteracted,
    VideoPaused,
    VideoPlayed,
    VideoSeeked,
    VideoTerminated,
)


@settings(max_examples=1)
@given(
    st.builds(
        VideoInitialized,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoInitializedVerbField),
        context=st.builds(VideoInitializedContextField),
    )
)
def test_models_xapi_video_initialized_with_valid_statement(statement):
    """Tests that a video initialized statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/initialized"


@settings(max_examples=1)
@given(
    st.builds(
        VideoInitialized,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoInitializedVerbField),
        context=st.builds(VideoInitializedContextField),
    )
)
def test_models_xapi_video_initialized_selector_with_valid_statement(statement):
    """Tests given a video initialized event, the get_model method should return VideoInitialized
    model."""

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.xapi").get_model(statement)
        is VideoInitialized
    )


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
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoPlayedVerbField),
        context=st.builds(VideoPlayedContextField),
        result=st.builds(VideoPlayedResultField),
    )
)
def test_models_xapi_video_played_with_valid_statement(statement):
    """Tests that a video played statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/played"


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
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoPlayedVerbField),
        context=st.builds(VideoPlayedContextField),
        result=st.builds(VideoPlayedResultField),
    )
)
def test_models_xapi_video_played_selector_with_valid_statement(statement):
    """Tests given a video played event, the get_model method should return VideoPlayed model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoPlayed


@settings(max_examples=1)
@given(
    st.builds(
        VideoPaused,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoPausedVerbField),
        context=st.builds(VideoPausedContextField),
        result=st.builds(VideoPausedResultField),
    )
)
def test_models_xapi_video_paused_with_valid_statement(statement):
    """Tests that a video paused statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/paused"


@settings(max_examples=1)
@given(
    st.builds(
        VideoPaused,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoPausedVerbField),
        context=st.builds(VideoPausedContextField),
        result=st.builds(VideoPausedResultField),
    )
)
def test_models_xapi_video_paused_selector_with_valid_statement(statement):
    """Tests given a video paused event, the get_model method should return VideoPaused model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoPaused


@settings(max_examples=1)
@given(
    st.builds(
        VideoSeeked,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoSeekedVerbField),
        context=st.builds(VideoSeekedContextField),
        result=st.builds(VideoSeekedResultField),
    )
)
def test_models_xapi_video_seeked_with_valid_statement(statement):
    """Tests that a video seeked statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/seeked"


@settings(max_examples=1)
@given(
    st.builds(
        VideoSeeked,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoSeekedVerbField),
        context=st.builds(VideoSeekedContextField),
        result=st.builds(VideoSeekedResultField),
    )
)
def test_models_xapi_video_seeked_selector_with_valid_statement(statement):
    """Tests given a video seeked event, the get_model method should return VideoSeeked model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoSeeked


@settings(max_examples=1)
@given(
    st.builds(
        VideoCompleted,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoCompletedVerbField),
        context=st.builds(VideoCompletedContextField),
        result=st.builds(VideoCompletedResultField),
    )
)
def test_models_xapi_video_completed_with_valid_statement(statement):
    """Tests that a video completed statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/completed"


@settings(max_examples=1)
@given(
    st.builds(
        VideoCompleted,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoCompletedVerbField),
        context=st.builds(VideoCompletedContextField),
        result=st.builds(VideoCompletedResultField),
    )
)
def test_models_xapi_video_completed_selector_with_valid_statement(statement):
    """Tests given a video completed event, the get_model method should return VideoCompleted
    model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoCompleted


@settings(max_examples=1)
@given(
    st.builds(
        VideoTerminated,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoTerminatedVerbField),
        context=st.builds(VideoTerminatedContextField),
        result=st.builds(VideoTerminatedResultField),
    )
)
def test_models_xapi_video_terminated_with_valid_statement(statement):
    """Tests that a video terminated statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"


@settings(max_examples=1)
@given(
    st.builds(
        VideoTerminated,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoTerminatedVerbField),
        context=st.builds(VideoTerminatedContextField),
        result=st.builds(VideoTerminatedResultField),
    )
)
def test_models_xapi_video_terminated_selector_with_valid_statement(statement):
    """Tests given a video terminated event, the get_model method should return VideoTerminated
    model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoTerminated


@settings(max_examples=1)
@given(
    st.builds(
        VideoInteracted,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoInteractedVerbField),
        context=st.builds(VideoInteractedContextField),
        result=st.builds(VideoInteractedResultField),
    )
)
def test_models_xapi_video_interacted_with_valid_statement(statement):
    """Tests that a video interacted statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/interacted"


@settings(max_examples=1)
@given(
    st.builds(
        VideoInteracted,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            VideoObjectField,
            definition=st.builds(VideoObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(VideoInteractedVerbField),
        context=st.builds(VideoInteractedContextField),
        result=st.builds(VideoInteractedResultField),
    )
)
def test_models_xapi_video_interacted_selector_with_valid_statement(statement):
    """Tests given a video interacted event, the get_model method should return VideoInteracted
    model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoInteracted
