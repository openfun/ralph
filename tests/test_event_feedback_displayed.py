"""
Tests for the FeedbackDisplayed event schema
"""
# pylint: disable=redefined-outer-name
import pandas as pd
import pytest
from marshmallow import ValidationError

from ralph.schemas.edx.feedback_displayed import FeedbackDisplayedSchema

from .fixtures.logs import EventType, _event

SCHEMA = FeedbackDisplayedSchema()
BULK_EVENTS = _event(50, EventType.FEEDBACK_DISPLAYED)


@pytest.fixture()
def feedback_displayed():
    """Returns a base event generator that generates size number of events"""
    return lambda size, **kwargs: _event(size, EventType.FEEDBACK_DISPLAYED, **kwargs)


def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid events does not raise exceptions
    """
    chunks = pd.read_json("tests/data/feedback_displayed.log", lines=True)
    try:
        for _, chunk in chunks.iterrows():
            SCHEMA.load(chunk.to_dict())
    except ValidationError:
        pytest.fail("valid feedback_displayed events should not raise exceptions")


def test_invalid_username_value(feedback_displayed):
    """ValidationError should be raised if the username value
    is empty or less than 2 characters
    """
    with pytest.raises(ValidationError):
        feedback_displayed(1, username="")
    with pytest.raises(ValidationError):
        feedback_displayed(1, username="1")
    with pytest.raises(ValidationError):
        feedback_displayed(1, username=1234)
    with pytest.raises(ValidationError):
        feedback_displayed(1, username="more_than_30_characters_long_for_sure")


def test_invalid_event_type_value(feedback_displayed):
    """ValidationError should be raised if the event_type value
    is not edx.problem.hint.feedback_displayed
    """
    with pytest.raises(ValidationError):
        feedback_displayed(1, event_type="problem_check")


def test_invalid_page_value(feedback_displayed):
    """ValidationError should be raised if the page value
    is not x_module
    """
    with pytest.raises(ValidationError):
        feedback_displayed(1, page="not_x_module")


def test_invalid_context_org_id_value(feedback_displayed):
    """ValidationError should be raised if the org_id value
    is not contained in the course_id
    """
    with pytest.raises(ValidationError):
        feedback_displayed(1, org_id="org_id_not_in_course_id")


def test_invalid_context_path_value(feedback_displayed):
    """ValidationError should be raised if the path value
    does not end with problem_check
    """
    context = feedback_displayed(1).iloc[0]["context"]
    context["path"] = "{}_not_problem_check".format(context["path"])
    with pytest.raises(ValidationError):
        feedback_displayed(1, context=context)


def test_invalid_event_question_type_value(feedback_displayed):
    """ValidationError should be raised if the event question_type value
    is not in the premitted value range
    """
    with pytest.raises(ValidationError):
        feedback_displayed(1, event_args={"question_type": "not_choiceresponse"})


def test_invalid_event_with_choice_all_missing(feedback_displayed):
    """ValidationError should be raised if the event question_type value
    is choiceresponse and event choice_all is missing
    """
    event = feedback_displayed(1, event_args={"question_type": "optionresponse"}).iloc[
        0
    ]["event"]
    event["question_type"] = "choiceresponse"
    with pytest.raises(ValidationError):
        feedback_displayed(1, event=event)
    # when the choice_all field is present the event should be valid
    event["choice_all"] = ["choice_1"]
    try:
        feedback_displayed(1, event=event)
    except ValidationError:
        pytest.fail("valid feedback_displayed events should not raise exceptions")


def test_invalid_event_with_choice_all_present(feedback_displayed):
    """ValidationError should be raised if the event choice_all field
    is present and the event question_type value is not "choiceresponse"
    """
    event = feedback_displayed(1, event_args={"question_type": "optionresponse"}).iloc[
        0
    ]["event"]
    event["choice_all"] = ["choice_1"]
    with pytest.raises(ValidationError):
        feedback_displayed(1, event=event)
