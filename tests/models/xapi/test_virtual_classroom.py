"""Tests for the `virtual classroom` xAPI profile."""

import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from pydantic import ValidationError

from ralph.models.selector import ModelSelector
from ralph.models.xapi.virtual_classroom.contexts import (
    VirtualClassroomContextContextActivities,
)
from ralph.models.xapi.virtual_classroom.statements import (
    VirtualClassroomAnsweredPoll,
    VirtualClassroomInitialized,
    VirtualClassroomJoined,
    VirtualClassroomLeft,
    VirtualClassroomLoweredHand,
    VirtualClassroomMuted,
    VirtualClassroomPostedPublicMessage,
    VirtualClassroomRaisedHand,
    VirtualClassroomSharedScreen,
    VirtualClassroomStartedCamera,
    VirtualClassroomStartedPoll,
    VirtualClassroomStoppedCamera,
    VirtualClassroomTerminated,
    VirtualClassroomUnmuted,
    VirtualClassroomUnsharedScreen,
)

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given
from tests.factories import mock_instance

@settings(deadline=None)
@pytest.mark.parametrize(
    "class_",
    [
        VirtualClassroomInitialized,
        VirtualClassroomJoined,
        VirtualClassroomLeft,
        VirtualClassroomTerminated,
        VirtualClassroomPostedPublicMessage,
        VirtualClassroomStartedPoll,
        VirtualClassroomAnsweredPoll,
        VirtualClassroomSharedScreen,
        VirtualClassroomUnsharedScreen,
        VirtualClassroomMuted,
        VirtualClassroomUnmuted,
        VirtualClassroomRaisedHand,
        VirtualClassroomLoweredHand,
        VirtualClassroomStartedCamera,
        VirtualClassroomStoppedCamera,
    ],
)
@custom_given(st.data())
def test_models_xapi_virtual_classroom_selectors_with_valid_statements(class_, data):
    """Test given a valid virtual classroom xAPI statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).json())
    model = ModelSelector(module="ralph.models.xapi").get_first_model(statement)
    assert model is class_


@custom_given(VirtualClassroomInitialized)
def test_models_xapi_virtual_classroom_initialized_with_valid_statement(statement):
    """Test that a valid virtual classroom initialized statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/initialized"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomJoined)
def test_models_xapi_virtual_classroom_joined_with_valid_statement(statement):
    """Test that a virtual classroom joined statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "http://activitystrea.ms/join"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomLeft)
def test_models_xapi_virtual_classroom_left_with_valid_statement(statement):
    """Test that a virtual classroom left statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "http://activitystrea.ms/leave"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomTerminated)
def test_models_xapi_virtual_classroom_terminated_with_valid_statement(statement):
    """Test that a virtual classroom terminated statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomMuted)
def test_models_xapi_virtual_classroom_muted_with_valid_statement(statement):
    """Test that a virtual classroom muted statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "https://w3id.org/xapi/virtual-classroom/verbs/muted"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomUnmuted)
def test_models_xapi_virtual_classroom_unmuted_with_valid_statement(statement):
    """Test that a virtual classroom unmuted statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "https://w3id.org/xapi/virtual-classroom/verbs/unmuted"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomSharedScreen)
def test_models_xapi_virtual_classroom_shared_screen_with_valid_statement(statement):
    """Test that a virtual classroom shared screen statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert (
        statement.verb.id
        == "https://w3id.org/xapi/virtual-classroom/verbs/shared-screen"
    )
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomUnsharedScreen)
def test_models_xapi_virtual_classroom_unshared_screen_with_valid_statement(statement):
    """Test that a virtual classroom unshared screen statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert (
        statement.verb.id
        == "https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen"
    )
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomStartedCamera)
def test_models_xapi_virtual_classroom_started_camera_with_valid_statement(statement):
    """Test that a virtual classroom started camera statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert (
        statement.verb.id
        == "https://w3id.org/xapi/virtual-classroom/verbs/started-camera"
    )
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomStoppedCamera)
def test_models_xapi_virtual_classroom_stopped_camera_with_valid_statement(statement):
    """Test that a virtual classroom stopped camera statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert (
        statement.verb.id
        == "https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera"
    )
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomRaisedHand)
def test_models_xapi_virtual_classroom_raised_hand_with_valid_statement(statement):
    """Test that a virtual classroom raised hand statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert (
        statement.verb.id == "https://w3id.org/xapi/virtual-classroom/verbs/raised-hand"
    )
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomLoweredHand)
def test_models_xapi_virtual_classroom_lowered_hand_with_valid_statement(statement):
    """Test that a virtual classroom lowered hand statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert (
        statement.verb.id
        == "https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand"
    )
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    )


@custom_given(VirtualClassroomStartedPoll)
def test_models_xapi_virtual_classroom_started_poll_with_valid_statement(statement):
    """Test that a virtual classroom started poll statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/asked"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )


@custom_given(VirtualClassroomAnsweredPoll)
def test_models_xapi_virtual_classroom_answered_poll_with_valid_statement(statement):
    """Test that a virtual classroom answered poll statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/answered"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )


@custom_given(VirtualClassroomPostedPublicMessage)
def test_models_xapi_virtual_classroom_posted_public_message_with_valid_statement(
    statement,
):
    """Test that a virtual classroom posted public message statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """
    assert statement.verb.id == "https://w3id.org/xapi/acrossx/verbs/posted"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/acrossx/activities/message"
    )


@settings(deadline=None)
@pytest.mark.parametrize(
    "category",
    [
        {"id": "https://w3id.org/xapi/virtual-classroom"},
        {
            "id": "https://w3id.org/xapi/virtual-classroom",
            "definition": {"type": "http://adlnet.gov/expapi/activities/profile"},
        },
        [{"id": "https://w3id.org/xapi/virtual-classroom"}],
        [{"id": "https://foo.bar"}, {"id": "https://w3id.org/xapi/virtual-classroom"}],
    ],
)
@custom_given(VirtualClassroomContextContextActivities)
def test_models_xapi_virtual_classroom_context_activities_with_valid_category(
    category, context_activities
):
    """Test that a valid `VirtualClassroomContextContextActivities` should not raise a
    `ValidationError`.
    """
    activities = json.loads(context_activities.json(exclude_none=True, by_alias=True))
    activities["category"] = category
    try:
        VirtualClassroomContextContextActivities(**activities)
    except ValidationError as err:
        pytest.fail(
            "Valid VirtualClassroomContextContextActivities should not raise "
            f"exceptions: {err}"
        )


@settings(deadline=None)
@pytest.mark.parametrize(
    "category",
    [
        {"id": "https://w3id.org/xapi/not-virtual-classroom"},
        {
            "id": "https://w3id.org/xapi/virtual-classroom",
            "definition": {"type": "http://adlnet.gov/expapi/activities/not-profile"},
        },
        [{"id": "https://w3id.org/xapi/not-virtual-classroom"}],
        [
            {"id": "https://foo.bar"},
            {"id": "https://w3id.org/xapi/not-virtual-classroom"},
        ],
    ],
)
@custom_given(VirtualClassroomContextContextActivities)
def test_models_xapi_virtual_classroom_context_activities_with_invalid_category(
    category, context_activities
):
    """Test that an invalid `VirtualClassroomContextContextActivities` should raise a
    `ValidationError`.
    """
    activities = json.loads(context_activities.json(exclude_none=True, by_alias=True))
    activities["category"] = category
    msg = (
        r"(The `context.contextActivities.category` field should contain at least one "
        r"valid `VirtualClassroomProfileActivity`) | (unexpected value)"
    )
    with pytest.raises(ValidationError, match=msg):
        VirtualClassroomContextContextActivities(**activities)
