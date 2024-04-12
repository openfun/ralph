"""Tests for the enrollment events xAPI converter."""

import json
from uuid import UUID, uuid5

import pytest

from ralph.models.converter import convert_dict_event
from ralph.models.edx.converters.xapi.enrollment import (
    EdxCourseEnrollmentActivatedToLMSRegisteredCourse,
    EdxCourseEnrollmentDeactivatedToLMSUnregisteredCourse,
)
from ralph.models.edx.enrollment.statements import (
    EdxCourseEnrollmentActivated,
    EdxCourseEnrollmentDeactivated,
)

from tests.factories import mock_instance, mock_url


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_enrollment_edx_course_enrollment_activated_to_lms_registered_course(  # noqa: E501
    uuid_namespace,
):
    """Test that converting with `EdxCourseEnrollmentActivatedToLMSRegisteredCourse`
    returns the expected xAPI statement.
    """
    event = mock_instance(EdxCourseEnrollmentActivated)
    platform_url = mock_url()

    event.event.course_id = "edX/DemoX/Demo_Course"
    event.context.user_id = "1"
    event_str = event.model_dump_json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event,
        event_str,
        EdxCourseEnrollmentActivatedToLMSRegisteredCourse(uuid_namespace, platform_url),
    )
    xapi_event_dict = json.loads(
        xapi_event.model_dump_json(exclude_none=True, by_alias=True)
    )

    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {"account": {"homePage": platform_url, "name": "1"}},
        "verb": {"id": "http://adlnet.gov/expapi/verbs/registered"},
        "context": {
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/lms",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
                        },
                    }
                ],
            },
        },
        "object": {
            "id": (
                f"{platform_url.rstrip('/')}/courses/"
                f"{event['event']['course_id']}/info"
            ),
            "definition": {
                "type": "http://adlnet.gov/expapi/activities/course",
            },
        },
        "timestamp": event["time"],
        "version": "1.0.0",
    }


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_enrollment_edx_course_enrollment_deactivated_to_lms_unregistered_course(  # noqa: E501
    uuid_namespace,
):
    """Test that converting with
    `EdxCourseEnrollmentDeactivatedToLMSUnregisteredCourse` returns the expected xAPI
    statement.
    """
    event = mock_instance(EdxCourseEnrollmentDeactivated)
    platform_url = mock_url()

    event.event.course_id = "edX/DemoX/Demo_Course"
    event.context.user_id = "1"
    event_str = event.model_dump_json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event,
        event_str,
        EdxCourseEnrollmentDeactivatedToLMSUnregisteredCourse(
            uuid_namespace, platform_url
        ),
    )
    xapi_event_dict = json.loads(
        xapi_event.model_dump_json(exclude_none=True, by_alias=True)
    )

    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {"account": {"homePage": platform_url, "name": "1"}},
        "verb": {"id": "http://id.tincanapi.com/verb/unregistered"},
        "context": {
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/lms",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
                        },
                    }
                ],
            },
        },
        "object": {
            "id": (
                f"{platform_url.rstrip('/')}/courses/"
                f"{event['event']['course_id']}/info"
            ),
            "definition": {
                "type": "http://adlnet.gov/expapi/activities/course",
            },
        },
        "timestamp": event["time"],
        "version": "1.0.0",
    }
