"""
Tests for the CreateSubmission event schema
"""
# pylint: disable=redefined-outer-name
import operator

import pytest
from marshmallow import ValidationError

from ralph.schemas.edx.ora.create_submission import CreateSubmissionSchema

from tests.fixtures.edx.ora.create_submission import CreateSubmissionType
from tests.fixtures.logs import EventType, _event
from tests.schema.edx.test_common import check_error, check_loading_valid_events


@pytest.fixture()
def create_submission():
    """Returns a save_submission event generator that generates size number of events"""
    return lambda size=1, **kwargs: _event(size, EventType.CREATE_SUBMISSION, **kwargs)


def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid events does not raise exceptions"""
    check_loading_valid_events(CreateSubmissionSchema(), "create_submission")


def test_invalid_event_type_value(create_submission):
    """ValidationError should be raised if the event_type value
    is not openassessmentblock.create_submission
    """
    with pytest.raises(ValidationError) as excinfo:
        create_submission(event_type="problem_check")
    check_error(
        excinfo,
        "The event event_type field is not `openassessmentblock.create_submission`",
    )


def test_invalid_context_path_value(create_submission):
    """ValidationError should be raised if the path value
    does not end with /submit
    """
    context = create_submission().iloc[0]["context"]
    context["path"] = "{}_not_submit".format(context["path"])
    with pytest.raises(ValidationError) as excinfo:
        create_submission(context=context)
    check_error(
        excinfo, "context.path should end with: /handler/submit", operator.contains,
    )


def test_valid_submission_event_with_submission_type_parameter(create_submission):
    """No Validation error should be raised for create submission events
    when setting the submission_type parameter.
    Check the expected behavior when the submission parameter is set.
    """
    try:
        event = create_submission(submission_type=CreateSubmissionType.FILE.value)
        assert len(event.iloc[0]["event"]["answer"]["parts"]) == 0
        event = create_submission(submission_type=CreateSubmissionType.TEXT.value)
        assert "file_keys" not in event.iloc[0]["event"]["answer"]
        assert "files_descriptions" not in event.iloc[0]["event"]["answer"]
        event = create_submission(
            submission_type=CreateSubmissionType.TEXT_AND_FILE.value
        )
    except ValidationError:
        pytest.fail("Valid base event ip address should not raise exceptions")
