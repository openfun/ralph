"""Tests for the `LMS` xAPI profile."""

import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from pydantic import ValidationError

from ralph.models.selector import ModelSelector
from ralph.models.xapi.lms.contexts import LMSContextContextActivities
from ralph.models.xapi.lms.statements import (
    LMSAccessedFile,
    LMSAccessedPage,
    LMSDownloadedAudio,
    LMSDownloadedDocument,
    LMSDownloadedFile,
    LMSDownloadedVideo,
    LMSRegisteredCourse,
    LMSUnregisteredCourse,
    LMSUploadedAudio,
    LMSUploadedDocument,
    LMSUploadedFile,
    LMSUploadedVideo,
)

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@settings(deadline=None)
@pytest.mark.parametrize(
    "class_",
    [
        LMSDownloadedVideo,
        LMSAccessedFile,
        LMSAccessedPage,
        LMSDownloadedFile,
        LMSUploadedFile,
        LMSRegisteredCourse,
        LMSUnregisteredCourse,
        LMSUploadedVideo,
        LMSDownloadedDocument,
        LMSUploadedDocument,
        LMSDownloadedAudio,
        LMSUploadedAudio,
    ],
)
@custom_given(st.data())
def test_models_xapi_lms_selectors_with_valid_statements(class_, data):
    """Test given a valid LMS xAPI statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.xapi").get_first_model(statement)
    assert model is class_


@custom_given(LMSRegisteredCourse)
def test_models_xapi_lms_registered_course_with_valid_statement(statement):
    """Test that a valid registered to a course statement has the expected `verb`.`id`
    and `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/registered"
    assert (
        statement.object.definition.type == "http://adlnet.gov/expapi/activities/course"
    )


@custom_given(LMSUnregisteredCourse)
def test_models_xapi_lms_unregistered_course_with_valid_statement(statement):
    """Test that a valid unregistered to a course statement has the expected
    `verb`.`id` and `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/unregistered"
    assert (
        statement.object.definition.type == "http://adlnet.gov/expapi/activities/course"
    )


@custom_given(LMSAccessedPage)
def test_models_xapi_lms_accessed_page_with_valid_statement(statement):
    """Test that a valid accessed a page statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/netc/verbs/accessed"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/acrossx/activities/webpage"
    )


@custom_given(LMSAccessedFile)
def test_models_xapi_lms_accessed_file_with_valid_statement(statement):
    """Test that a valid accessed a file statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/netc/verbs/accessed"
    assert statement.object.definition.type == "http://activitystrea.ms/file"


@custom_given(LMSUploadedFile)
def test_models_xapi_lms_uploaded_file_with_valid_statement(statement):
    """Test that a valid uploaded a file statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/netc/verbs/uploaded"
    assert statement.object.definition.type == "http://activitystrea.ms/file"


@custom_given(LMSDownloadedFile)
def test_models_xapi_lms_downloaded_file_with_valid_statement(statement):
    """Test that a valid downloaded a file statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/downloaded"
    assert statement.object.definition.type == "http://activitystrea.ms/file"


@custom_given(LMSDownloadedVideo)
def test_models_xapi_lms_downloaded_video_with_valid_statement(statement):
    """Test that a valid downloaded a video statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/downloaded"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(LMSUploadedVideo)
def test_models_xapi_lms_uploaded_video_with_valid_statement(statement):
    """Test that a valid uploaded a video statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/netc/verbs/uploaded"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/video/activity-type/video"
    )


@custom_given(LMSDownloadedDocument)
def test_models_xapi_lms_downloaded_document_with_valid_statement(statement):
    """Test that a valid downloaded a document statement has the expected `verb`.`id`
    and `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/downloaded"
    assert (
        statement.object.definition.type
        == "http://id.tincanapi.com/activitytype/document"
    )


@custom_given(LMSUploadedDocument)
def test_models_xapi_lms_uploaded_document_with_valid_statement(statement):
    """Test that a valid uploaded a document statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/netc/verbs/uploaded"
    assert (
        statement.object.definition.type
        == "http://id.tincanapi.com/activitytype/document"
    )


@custom_given(LMSDownloadedAudio)
def test_models_xapi_lms_downloaded_audio_with_valid_statement(statement):
    """Test that a valid downloaded an audio statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://id.tincanapi.com/verb/downloaded"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/audio/activity-type/audio"
    )


@custom_given(LMSUploadedAudio)
def test_models_xapi_lms_uploaded_audio_with_valid_statement(statement):
    """Test that a valid uploaded an audio statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "https://w3id.org/xapi/netc/verbs/uploaded"
    assert (
        statement.object.definition.type
        == "https://w3id.org/xapi/audio/activity-type/audio"
    )


@settings(deadline=None)
@pytest.mark.parametrize(
    "category",
    [
        {"id": "https://w3id.org/xapi/lms"},
        {
            "id": "https://w3id.org/xapi/lms",
            "definition": {"type": "http://adlnet.gov/expapi/activities/profile"},
        },
        [{"id": "https://w3id.org/xapi/lms"}],
        [{"id": "https://foo.bar"}, {"id": "https://w3id.org/xapi/lms"}],
    ],
)
@custom_given(LMSContextContextActivities)
def test_models_xapi_lms_context_context_activities_with_valid_category(
    category, context_activities
):
    """Test that a valid `LMSContextContextActivities` should not raise a
    `ValidationError`.
    """
    activities = json.loads(context_activities.json(exclude_none=True, by_alias=True))
    activities["category"] = category
    try:
        LMSContextContextActivities(**activities)
    except ValidationError as err:
        pytest.fail(
            f"Valid LMSContextContextActivities should not raise exceptions: {err}"
        )


@settings(deadline=None)
@pytest.mark.parametrize(
    "category",
    [
        {"id": "https://w3id.org/xapi/not-lms"},
        {
            "id": "https://w3id.org/xapi/lms",
            "definition": {"type": "http://adlnet.gov/expapi/activities/not-profile"},
        },
        [{"id": "https://w3id.org/xapi/not-lms"}],
        [{"id": "https://foo.bar"}, {"id": "https://w3id.org/xapi/not-lms"}],
    ],
)
@custom_given(LMSContextContextActivities)
def test_models_xapi_lms_context_context_activities_with_invalid_category(
    category, context_activities
):
    """Test that an invalid `LMSContextContextActivities` should raise a
    `ValidationError`.
    """
    activities = json.loads(context_activities.json(exclude_none=True, by_alias=True))
    activities["category"] = category
    msg = (
        r"(The `context.contextActivities.category` field should contain at least one "
        r"valid `LMSProfileActivity`) | (unexpected value)"
    )
    with pytest.raises(ValidationError, match=msg):
        LMSContextContextActivities(**activities)
