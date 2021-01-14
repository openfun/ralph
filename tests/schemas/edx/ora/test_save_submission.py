"""Tests for the SaveSubmission event schema"""

# pylint: disable=redefined-outer-name
import operator

import pytest
from marshmallow import ValidationError

from tests.fixtures.logs import EventType, event_generator
from tests.schemas.edx.test_common import check_error


@pytest.fixture()
def save_submission():
    """Returns a save_submission event generator that generates size number of events"""
    return lambda **kwargs: event_generator(EventType.SAVE_SUBMISSION, **kwargs)


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
    context = save_submission()["context"]
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
    is not a parsable JSON containing the key `parts` or the corresponding
    value is not a array of JSON objects containing the  key `text`
    """
    with pytest.raises(ValidationError) as excinfo:
        save_submission(event="not a parsable JSON string")
    check_error(excinfo, "Invalid input type.")
