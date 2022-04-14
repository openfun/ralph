"""Tests for the xAPI played statement"""

import json

from ralph.models.selector import ModelSelector
from ralph.models.xapi.video.statements import (
    VideoCompleted,
    VideoInitialized,
    VideoInteracted,
    VideoPaused,
    VideoPlayed,
    VideoSeeked,
    VideoTerminated,
)

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(VideoInitialized)
def test_models_xapi_video_initialized_with_valid_statement(statement):
    """Tests that a video initialized statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/initialized"


@custom_given(VideoInitialized)
def test_models_xapi_video_initialized_selector_with_valid_statement(statement):
    """Tests given a video initialized event, the get_model method should return
    VideoInitialized model."""

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.xapi").get_model(statement)
        is VideoInitialized
    )


@custom_given(VideoPlayed)
def test_models_xapi_video_played_with_valid_statement(statement):
    """Tests that a video played statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/played"


@custom_given(VideoPlayed)
def test_models_xapi_video_played_selector_with_valid_statement(statement):
    """Tests given a video played event, the get_model method should return
    VideoPlayed model.
    """

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoPlayed


@custom_given(VideoPaused)
def test_models_xapi_video_paused_with_valid_statement(statement):
    """Tests that a video paused statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/paused"


@custom_given(VideoPaused)
def test_models_xapi_video_paused_selector_with_valid_statement(statement):
    """Tests given a video paused event, the get_model method should return VideoPaused
    model.
    """

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoPaused


@custom_given(VideoSeeked)
def test_models_xapi_video_seeked_with_valid_statement(statement):
    """Tests that a video seeked statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/seeked"


@custom_given(VideoSeeked)
def test_models_xapi_video_seeked_selector_with_valid_statement(statement):
    """Tests given a video seeked event, the get_model method should return VideoSeeked
    model.
    """

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoSeeked


@custom_given(VideoCompleted)
def test_models_xapi_video_completed_with_valid_statement(statement):
    """Tests that a video completed statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/completed"


@custom_given(VideoCompleted)
def test_models_xapi_video_completed_selector_with_valid_statement(statement):
    """Tests given a video completed event, the get_model method should return
    VideoCompleted model.
    """

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoCompleted


@custom_given(VideoTerminated)
def test_models_xapi_video_terminated_with_valid_statement(statement):
    """Tests that a video terminated statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"


@custom_given(VideoTerminated)
def test_models_xapi_video_terminated_selector_with_valid_statement(statement):
    """Tests given a video terminated event, the get_model method should return
    VideoTerminated model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoTerminated


@custom_given(VideoInteracted)
def test_models_xapi_video_interacted_with_valid_statement(statement):
    """Tests that a video interacted statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/interacted"


@custom_given(VideoInteracted)
def test_models_xapi_video_interacted_selector_with_valid_statement(statement):
    """Tests given a video interacted event, the get_model method should return
    VideoInteracted model."""

    event = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.xapi").get_model(event) is VideoInteracted
