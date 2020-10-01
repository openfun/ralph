"""
Tests for the SaveSubmission event schema
"""
# pylint: disable=redefined-outer-name
import operator

import pytest
from marshmallow import ValidationError

from ralph.schemas.edx.ora.save_submission import SaveSubmissionSchema

from tests.fixtures.logs import EventType, _event
from tests.schema.edx.test_common import check_error, check_loading_valid_events


@pytest.fixture()
def save_submission():
    """Returns a save_submission event generator that generates size number of events"""
    return lambda size=1, **kwargs: _event(size, EventType.SAVE_SUBMISSION, **kwargs)


def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid events does not raise exceptions"""
    check_loading_valid_events(SaveSubmissionSchema(), "save_submission")


def test_invalid_event_type_value(save_submission):
    """ValidationError should be raised if the event_type value
    is not openassessmentblock.save_submission
    """
    with pytest.raises(ValidationError) as excinfo:
        save_submission(event_type="problem_check")
    check_error(
        excinfo,
        "The event event_type field is not `openassessmentblock.save_submission`",
    )


def test_invalid_context_path_value(save_submission):
    """ValidationError should be raised if the path value
    does not end with /save_submission
    """
    context = save_submission(1).iloc[0]["context"]
    context["path"] = "{}_not_save_submission".format(context["path"])
    with pytest.raises(ValidationError) as excinfo:
        save_submission(context=context)
    check_error(
        excinfo,
        "context.path should end with: /handler/save_submission",
        operator.contains,
    )


def test_invalid_event_value(save_submission):
    """Validation error should be raised if the event field value
    is not a parsable json containing the key `parts` or the corresponding
    value is not a array of json objects containing the  key `text`
    """
    with pytest.raises(ValidationError) as excinfo:
        save_submission(event="not a parsable json string")
    check_error(excinfo, "Invalid input type.")
