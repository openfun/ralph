"""Tests for the video event xAPI converter"""

import json
from uuid import UUID, uuid5

import pytest

from ralph.models.converter import convert_dict_event
from ralph.models.edx.converters.xapi.video import (
    UILoadVideoToVideoInitialized,
    UIPauseVideoToVideoPaused,
    UIPlayVideoToVideoPlayed,
    UISeekVideoToVideoSeeked,
    UIStopVideoToVideoTerminated,
)
from ralph.models.edx.video.statements import (
    UILoadVideo,
    UIPauseVideo,
    UIPlayVideo,
    UISeekVideo,
    UIStopVideo,
)

from tests.factories import mock_instance, mock_url


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_video_ui_load_video_to_video_initialized(
    uuid_namespace,
):
    """Test that converting with `UILoadVideoToVideoInitialized` returns the
    expected xAPI statement.
    """
    event = mock_instance(UILoadVideo)
    event.context.course_id = "course-v1:a+b+c"

    platform_url = mock_url()

    event.context.user_id = "1"
    event.session = "af45a0e650c4a4fdb0bcde75a1e4b694"
    session_uuid = "af45a0e6-50c4-a4fd-b0bc-de75a1e4b694"
    event_str = event.model_dump_json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, UILoadVideoToVideoInitialized(uuid_namespace, platform_url)
    )
    xapi_event_dict = json.loads(
        xapi_event.model_dump_json(exclude_none=True, by_alias=True)
    )

    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": platform_url, "name": "1"},
            "objectType": "Agent",
        },
        "verb": {"id": "http://adlnet.gov/expapi/verbs/initialized"},
        "context": {
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
                        },
                    }
                ],
            },
            "extensions": {
                "https://w3id.org/xapi/video/extensions/length": 0.0,
                "https://w3id.org/xapi/video/extensions/session-id": session_uuid,
                "https://w3id.org/xapi/video/extensions/user-agent": event["agent"],
            },
        },
        "object": {
            "id": platform_url.rstrip("/")
            + "/xblock/block-v1:"
            + event["context"]["course_id"]
            + "-course-v1:+type@video+block@"
            + event["event"]["id"],
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": event["event"]["id"]},
            },
        },
        "timestamp": event["time"],
        "version": "1.0.0",
    }


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_video_ui_play_video_to_video_played(uuid_namespace):
    """Test that converting with `UIPlayVideoToVideoPlayed` returns the expected
    xAPI statement.
    """
    event = mock_instance(UIPlayVideo)
    event.context.course_id = "course-v1:a+b+c"

    platform_url = mock_url()

    event.context.user_id = "1"
    event.session = "af45a0e650c4a4fdb0bcde75a1e4b694"
    session_uuid = "af45a0e6-50c4-a4fd-b0bc-de75a1e4b694"
    event_str = event.model_dump_json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, UIPlayVideoToVideoPlayed(uuid_namespace, platform_url)
    )
    xapi_event_dict = json.loads(
        xapi_event.model_dump_json(exclude_none=True, by_alias=True)
    )
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": platform_url, "name": "1"},
            "objectType": "Agent",
        },
        "verb": {"id": "https://w3id.org/xapi/video/verbs/played"},
        "object": {
            "id": platform_url.rstrip("/")
            + "/xblock/block-v1:"
            + event["context"]["course_id"]
            + "-course-v1:+type@video+block@"
            + event["event"]["id"],
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": event["event"]["id"]},
            },
        },
        "result": {
            "extensions": {
                "https://w3id.org/xapi/video/extensions/time": event["event"][
                    "currentTime"
                ]
            }
        },
        "context": {
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
                        },
                    }
                ],
            },
            "extensions": {
                "https://w3id.org/xapi/video/extensions/session-id": session_uuid,
            },
        },
        "timestamp": event["time"],
        "version": "1.0.0",
    }


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_video_ui_pause_video_to_video_paused(
    uuid_namespace,
):
    """Test that converting with `UIPauseVideoToVideoPaused` returns the expected xAPI
    statement.
    """
    event = mock_instance(UIPauseVideo)
    event.context.course_id = "course-v1:a+b+c"

    platform_url = mock_url()

    event.context.user_id = "1"
    event.session = "af45a0e650c4a4fdb0bcde75a1e4b694"
    session_uuid = "af45a0e6-50c4-a4fd-b0bc-de75a1e4b694"
    event_str = event.model_dump_json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, UIPauseVideoToVideoPaused(uuid_namespace, platform_url)
    )
    xapi_event_dict = json.loads(
        xapi_event.model_dump_json(exclude_none=True, by_alias=True)
    )
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": platform_url, "name": "1"},
            "objectType": "Agent",
        },
        "verb": {"id": "https://w3id.org/xapi/video/verbs/paused"},
        "object": {
            "id": platform_url.rstrip("/")
            + "/xblock/block-v1:"
            + event["context"]["course_id"]
            + "-course-v1:+type@video+block@"
            + event["event"]["id"],
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": event["event"]["id"]},
            },
        },
        "context": {
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
                        },
                    }
                ],
            },
            "extensions": {
                "https://w3id.org/xapi/video/extensions/length": 0.0,
                "https://w3id.org/xapi/video/extensions/session-id": session_uuid,
            },
        },
        "result": {
            "extensions": {
                "https://w3id.org/xapi/video/extensions/time": event["event"][
                    "currentTime"
                ]
            }
        },
        "timestamp": event["time"],
        "version": "1.0.0",
    }


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_video_ui_stop_video_to_video_terminated(
    uuid_namespace,
):
    """Test that converting with `UIStopVideoToVideoTerminated` returns the expected
    xAPI statement.
    """
    event = mock_instance(UIStopVideo)
    event.context.course_id = "course-v1:a+b+c"

    platform_url = mock_url()

    event.context.user_id = "1"
    event.session = "af45a0e650c4a4fdb0bcde75a1e4b694"
    session_uuid = "af45a0e6-50c4-a4fd-b0bc-de75a1e4b694"
    event_str = event.model_dump_json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, UIStopVideoToVideoTerminated(uuid_namespace, platform_url)
    )
    xapi_event_dict = json.loads(
        xapi_event.model_dump_json(exclude_none=True, by_alias=True)
    )
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": platform_url, "name": "1"},
            "objectType": "Agent",
        },
        "verb": {"id": "http://adlnet.gov/expapi/verbs/terminated"},
        "object": {
            "id": platform_url.rstrip("/")
            + "/xblock/block-v1:"
            + event["context"]["course_id"]
            + "-course-v1:+type@video+block@"
            + event["event"]["id"],
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": event["event"]["id"]},
            },
        },
        "context": {
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
                        },
                    }
                ],
            },
            "extensions": {
                "https://w3id.org/xapi/video/extensions/length": 0.0,
                "https://w3id.org/xapi/video/extensions/session-id": session_uuid,
            },
        },
        "result": {
            "extensions": {
                "https://w3id.org/xapi/video/extensions/time": event["event"][
                    "currentTime"
                ],
                "https://w3id.org/xapi/video/extensions/progress": 0.0,
            }
        },
        "timestamp": event["time"],
        "version": "1.0.0",
    }


@pytest.mark.parametrize("uuid_namespace", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_models_edx_converters_xapi_video_ui_seek_video_to_video_seeked(uuid_namespace):
    """Test that converting with `UISeekVideoToVideoSeeked` returns the expected
    xAPI statement.
    """
    event = mock_instance(UISeekVideo)
    event.context.course_id = "course-v1:a+b+c"

    platform_url = mock_url()

    event.context.user_id = "1"
    event.session = "af45a0e650c4a4fdb0bcde75a1e4b694"
    session_uuid = "af45a0e6-50c4-a4fd-b0bc-de75a1e4b694"
    event_str = event.model_dump_json()
    event = json.loads(event_str)
    xapi_event = convert_dict_event(
        event, event_str, UISeekVideoToVideoSeeked(uuid_namespace, platform_url)
    )
    xapi_event_dict = json.loads(
        xapi_event.model_dump_json(exclude_none=True, by_alias=True)
    )
    assert xapi_event_dict == {
        "id": str(uuid5(UUID(uuid_namespace), event_str)),
        "actor": {
            "account": {"homePage": platform_url, "name": "1"},
            "objectType": "Agent",
        },
        "verb": {"id": "https://w3id.org/xapi/video/verbs/seeked"},
        "object": {
            "id": platform_url.rstrip("/")
            + "/xblock/block-v1:"
            + event["context"]["course_id"]
            + "-course-v1:+type@video+block@"
            + event["event"]["id"],
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": event["event"]["id"]},
            },
        },
        "result": {
            "extensions": {
                "https://w3id.org/xapi/video/extensions/time-from": event["event"][
                    "old_time"
                ],
                "https://w3id.org/xapi/video/extensions/time-to": event["event"][
                    "new_time"
                ],
            }
        },
        "context": {
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
                        },
                    }
                ],
            },
            "extensions": {
                "https://w3id.org/xapi/video/extensions/session-id": session_uuid,
            },
        },
        "timestamp": event["time"],
        "version": "1.0.0",
    }
