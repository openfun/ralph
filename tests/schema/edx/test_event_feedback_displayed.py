"""
Tests for the FeedbackDisplayed event schema
"""
# pylint: disable=redefined-outer-name
import operator

import pytest
from marshmallow import ValidationError

from ralph.schemas.edx.feedback_displayed import FeedbackDisplayedSchema

from tests.fixtures.logs import EventType, _event

from .test_common import check_error, check_loading_valid_events


@pytest.fixture()
def feedback_displayed():
    """Returns a base event generator that generates size number of events"""
    return lambda size=1, **kwargs: _event(size, EventType.FEEDBACK_DISPLAYED, **kwargs)


def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid events does not raise exceptions"""
    check_loading_valid_events(FeedbackDisplayedSchema(), "feedback_displayed")


def test_invalid_username_value(feedback_displayed):
    """ValidationError should be raised if the username value
    is empty or less than 2 characters
    """
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(username="")
    check_error(excinfo, "Length must be between 2 and 30.")
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(username="1")
    check_error(excinfo, "Length must be between 2 and 30.")
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(username=1234)
    check_error(excinfo, "Not a valid string.")
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(username="more_than_30_characters_long_for_sure")
    check_error(excinfo, "Length must be between 2 and 30.")


def test_invalid_event_type_value(feedback_displayed):
    """ValidationError should be raised if the event_type value
    is not edx.problem.hint.feedback_displayed
    """
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(event_type="problem_check")
    check_error(
        excinfo,
        "The event event_type field is not `edx.problem.hint.feedback_displayed`",
    )


def test_invalid_page_value(feedback_displayed):
    """ValidationError should be raised if the page value
    is not x_module
    """
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(page="not_x_module")
    check_error(excinfo, "The event page field is not `x_module`")


def test_invalid_context_org_id_value(feedback_displayed):
    """ValidationError should be raised if the org_id value
    is not contained in the course_id
    """
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(
            1,
            context_args={
                "org_id": "org_id_not_in_course_id",
                "course_id": "course-v1:org_id+course+session",
            },
        )
    check_error(
        excinfo, "organization ID in the course ID does not match", operator.contains
    )


def test_invalid_context_path_value(feedback_displayed):
    """ValidationError should be raised if the path value
    does not end with problem_check
    """
    context = feedback_displayed(1).iloc[0]["context"]
    context["path"] = "{}_not_problem_check".format(context["path"])
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(context=context)
    check_error(
        excinfo,
        "context.path should end with: xmodule_handler/problem_check",
        operator.contains,
    )


def test_invalid_event_question_type_value(feedback_displayed):
    """ValidationError should be raised if the event question_type value
    is not in the premitted value range
    """
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(event_args={"question_type": "not_choiceresponse"})
    check_error(excinfo, "Not allowed value")


def test_invalid_event_with_choice_all_missing(feedback_displayed):
    """ValidationError should be raised if the event question_type value
    is choiceresponse and event choice_all is missing
    """
    event = feedback_displayed(event_args={"question_type": "optionresponse"}).iloc[0][
        "event"
    ]
    event["question_type"] = "choiceresponse"
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(event=event)
    check_error(
        excinfo,
        "When the question_type is `choiceresponse`, choice_all should be present",
    )
    event["choice_all"] = ["choice_1"]
    try:
        feedback_displayed(event=event)
    except ValidationError:
        pytest.fail("valid feedback_displayed events should not raise exceptions")


def test_invalid_event_with_choice_all_present(feedback_displayed):
    """ValidationError should be raised if the event choice_all field
    is present and the event question_type value is not "choiceresponse"
    """
    event = feedback_displayed(event_args={"question_type": "optionresponse"}).iloc[0][
        "event"
    ]
    event["choice_all"] = ["choice_1"]
    with pytest.raises(ValidationError) as excinfo:
        feedback_displayed(event=event)
    check_error(
        excinfo,
        "choice_all should be only present when the question_type is `choiceresponse`",
    )
