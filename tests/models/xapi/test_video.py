"""Tests for the `video` xAPI profile."""

import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from pydantic import ValidationError

from ralph.models.selector import ModelSelector
from ralph.models.validator import Validator
from ralph.models.xapi.video.contexts import VideoContextContextActivities
from ralph.models.xapi.video.statements import (
    VideoCompleted,
    VideoEnableClosedCaptioning,
    VideoInitialized,
    VideoPaused,
    VideoPlayed,
    VideoScreenChangeInteraction,
    VideoSeeked,
    VideoTerminated,
    VideoVolumeChangeInteraction,
)

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given

from tests.factories import mock_instance

@pytest.mark.parametrize(
    "class_",
    [
        VideoCompleted,
        VideoInitialized,
        VideoPaused,
        VideoPlayed,
        VideoSeeked,
        VideoTerminated,
    ],
)
def test_models_xapi_video_selectors_with_valid_statements(class_):
    """Test given a valid video xAPI statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).json())
    model = ModelSelector(module="ralph.models.xapi").get_first_model(statement)
    assert model is class_


@settings(deadline=None)
@pytest.mark.parametrize(
    "class_",
    [
        VideoVolumeChangeInteraction,
        VideoEnableClosedCaptioning,
        VideoScreenChangeInteraction,
    ],
)
@custom_given(st.data())
def test_models_xapi_video_interaction_validator_with_valid_statements(class_, data):
    """Test given a valid video interaction xAPI statement the `get_first_valid_model`
    validator method should return the expected model.
    """

    statement = json.loads(
        data.draw(custom_builds(class_)).json(exclude_none=True, by_alias=True)
    )

    model = Validator(ModelSelector(module="ralph.models.xapi")).get_first_valid_model(
        statement
    )

    assert isinstance(model, class_)


@custom_given(VideoInitialized)
def test_models_xapi_video_initialized_with_valid_statement(statement):
    """Test that a valid video initialized statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/initialized"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoPlayed)
def test_models_xapi_video_played_with_valid_statement(statement):
    """Test that a valid video played statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/played"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoPaused)
def test_models_xapi_video_paused_with_valid_statement(statement):
    """Test that a video paused statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/paused"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoSeeked)
def test_models_xapi_video_seeked_with_valid_statement(statement):
    """Test that a video seeked statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/video/verbs/seeked"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoCompleted)
def test_models_xapi_video_completed_with_valid_statement(statement):
    """Test that a video completed statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/completed"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoTerminated)
def test_models_xapi_video_terminated_with_valid_statement(statement):
    """Test that a video terminated statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoEnableClosedCaptioning)
def test_models_xapi_video_enable_closed_captioning_with_valid_statement(statement):
    """Test that a video enable closed captioning statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/interacted"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoVolumeChangeInteraction)
def test_models_xapi_video_volume_change_interaction_with_valid_statement(statement):
    """Test that a video volume change interaction statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/interacted"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(VideoScreenChangeInteraction)
def test_models_xapi_video_screen_change_interaction_with_valid_statement(statement):
    """Test that a video screen change interaction statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/interacted"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@settings(deadline=None)
@pytest.mark.parametrize(
    "category",
    [
        {"id": "https://w3id.org/xapi/video"},
        {
            "id": "https://w3id.org/xapi/video",
            "definition": {"type": "http://adlnet.gov/expapi/activities/profile"},
        },
        [{"id": "https://w3id.org/xapi/video"}],
        [{"id": "https://foo.bar"}, {"id": "https://w3id.org/xapi/video"}],
    ],
)
@custom_given(VideoContextContextActivities)
def test_models_xapi_video_context_activities_with_valid_category(
    category, context_activities
):
    """Test that a valid `VideoContextContextActivities` should not raise a
    `ValidationError`.
    """
    activities = json.loads(context_activities.json(exclude_none=True, by_alias=True))
    activities["category"] = category
    try:
        VideoContextContextActivities(**activities)
    except ValidationError as err:
        pytest.fail(
            f"Valid VideoContextContextActivities should not raise exceptions: {err}"
        )


@settings(deadline=None)
@pytest.mark.parametrize(
    "category",
    [
        {"id": "https://w3id.org/xapi/not-video"},
        {
            "id": "https://w3id.org/xapi/video",
            "definition": {"type": "http://adlnet.gov/expapi/activities/not-profile"},
        },
        [{"id": "https://w3id.org/xapi/not-video"}],
        [{"id": "https://foo.bar"}, {"id": "https://w3id.org/xapi/not-video"}],
    ],
)
@custom_given(VideoContextContextActivities)
def test_models_xapi_video_context_activities_with_invalid_category(
    category, context_activities
):
    """Test that an invalid `VideoContextContextActivities` should raise a
    `ValidationError`.
    """
    activities = json.loads(context_activities.json(exclude_none=True, by_alias=True))
    activities["category"] = category
    msg = (
        r"(The `context.contextActivities.category` field should contain at least one "
        r"valid `VideoProfileActivity`) | (unexpected value)"
    )
    with pytest.raises(ValidationError, match=msg):
        VideoContextContextActivities(**activities)
