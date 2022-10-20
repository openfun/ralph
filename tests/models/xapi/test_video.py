"""Tests for the xAPI played statement"""

import json

import pytest
from hypothesis import strategies as st

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

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [
        VideoCompleted,
        VideoInitialized,
        VideoInteracted,
        VideoPaused,
        VideoPlayed,
        VideoSeeked,
        VideoTerminated,
    ],
)
@custom_given(st.data())
def test_models_xapi_video_selectors_with_valid_statements(class_, data):
    """Tests given a valid video xAPI statement the `get_first_model`
    selector method should return the expected model.
    """

    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.xapi").get_first_model(statement)
    assert model is class_


@custom_given(VideoInitialized)
def test_models_xapi_video_initialized_with_valid_statement(statement):
    """Tests that a video initialized statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/initialized"


@custom_given(VideoPlayed)
def test_models_xapi_video_played_with_valid_statement(statement):
    """Tests that a video played statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/played"


@custom_given(VideoPaused)
def test_models_xapi_video_paused_with_valid_statement(statement):
    """Tests that a video paused statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/paused"


@custom_given(VideoSeeked)
def test_models_xapi_video_seeked_with_valid_statement(statement):
    """Tests that a video seeked statement has the expected verb.id."""

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/seeked"


@custom_given(VideoCompleted)
def test_models_xapi_video_completed_with_valid_statement(statement):
    """Tests that a video completed statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/completed"


@custom_given(VideoTerminated)
def test_models_xapi_video_terminated_with_valid_statement(statement):
    """Tests that a video terminated statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"


@custom_given(VideoInteracted)
def test_models_xapi_video_interacted_with_valid_statement(statement):
    """Tests that a video interacted statement has the expected verb.id."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/interacted"
