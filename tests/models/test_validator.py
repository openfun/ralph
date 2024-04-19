"""Tests for the event validator."""

import copy
import json
import logging

import pytest
from pydantic import ValidationError, create_model

from ralph.exceptions import BadFormatException, UnknownEventException
from ralph.models.edx.navigational.statements import UIPageClose
from ralph.models.edx.server import Server
from ralph.models.selector import ModelSelector
from ralph.models.validator import Validator

from tests.factories import mock_instance


def test_models_validator_validate_with_no_events(caplog):
    """Test given no events, the validate method does not write error messages."""
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        [], ignore_errors=False, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    assert [] == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize("event", ["", 1, None, {}])
def test_models_validator_validate_with_a_non_json_event_writes_an_error_message(
    event, caplog
):
    """Test given a non JSON event, the validate method should write an error
    message.
    """
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        [event], ignore_errors=True, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    errors = ["Input event is not a valid JSON string"]
    assert errors == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize("event", ["", 1, None, {}])
def test_models_validator_validate_with_a_non_json_event_raises_an_exception(
    event, caplog
):
    """Test given a non JSON event, the validate method should raise a
    BadFormatException.
    """
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        [event], ignore_errors=False, fail_on_unknown=True
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BadFormatException):
            list(result)


@pytest.mark.parametrize(
    "event",
    [
        json.dumps({}),
        json.dumps({"event_source": "browser"}),
        json.dumps({"event_source": "browser", "event_type": None}),
    ],
)
def test_models_validator_validate_with_an_unknown_event_writes_an_error_message(
    event, caplog
):
    """Test given an unknown event the validate method should write an error
    message.
    """
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        [event],
        ignore_errors=False,
        fail_on_unknown=False,
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    errors = ["No matching pydantic model found for input event"]
    assert errors == [message for _, _, message in caplog.record_tuples]


@pytest.mark.parametrize(
    "event",
    [
        json.dumps({}),
        json.dumps({"event_source": "browser"}),
        json.dumps({"event_source": "browser", "event_type": None}),
    ],
)
def test_models_validator_validate_with_an_unknown_event_raises_an_exception(
    event, caplog
):
    """Test given an unknown event the validate method should raise an
    UnknownEventException.
    """
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        [event],
        ignore_errors=False,
        fail_on_unknown=True,
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(UnknownEventException):
            list(result)


def test_models_validator_validate_with_an_invalid_page_close_event_writes_an_error_message(  # noqa
    caplog,
):
    """Test given an event that match a pydantic model but fail at the model validation
    step, the validate method should write an error message.
    """
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        [json.dumps({"event_source": "browser", "event_type": "page_close"})],
        ignore_errors=True,
        fail_on_unknown=True,
    )
    with caplog.at_level(logging.ERROR):
        assert not list(result)
    errors = ["Input event is not valid."]
    assert errors == [message for _, _, message in caplog.record_tuples]


def test_models_validator_validate_with_invalid_page_close_event_raises_an_exception(
    caplog,
):
    """Test given an event that match a pydantic model but fail at the model validation
    step, the validate method should raise a BadFormatException.
    """
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        [json.dumps({"event_source": "browser", "event_type": "page_close"})],
        ignore_errors=False,
        fail_on_unknown=True,
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BadFormatException):
            list(result)


@pytest.mark.parametrize("ignore_errors", [True, False])
@pytest.mark.parametrize("fail_on_unknown", [True, False])
def test_models_validator_validate_with_valid_events(ignore_errors, fail_on_unknown):
    """Test given a valid event the validate method should yield it."""
    event = mock_instance(UIPageClose)

    event_str = event.model_dump_json()
    event_dict = json.loads(event_str)
    validator = Validator(ModelSelector(module="ralph.models.edx"))
    result = validator.validate([event_str], ignore_errors, fail_on_unknown)
    assert json.loads(next(result)) == event_dict


def test_models_validator_validate_counter(caplog):
    """Test given multiple events the validate method
    should log the total and invalid events.
    """
    event = mock_instance(UIPageClose)

    valid_event = event.model_dump_json()
    invalid_event_1 = 1
    invalid_event_2 = ""
    events = [invalid_event_1, valid_event, invalid_event_2]
    result = Validator(ModelSelector(module="ralph.models.edx")).validate(
        events, ignore_errors=True, fail_on_unknown=False
    )
    with caplog.at_level(logging.INFO):
        assert [valid_event] == list(result)
    assert (
        "ralph.models.validator",
        logging.INFO,
        "Total events: 3, Invalid events: 2",
    ) in caplog.record_tuples


def test_models_validator_validate_typing_cleanup():
    """Test given a valid event with wrong field types, the validate method should fix
    them.
    """
    event = mock_instance(Server)

    valid_event_str = event.model_dump_json()
    valid_event = json.loads(valid_event_str)
    valid_event["host"] = "1"
    valid_event["accept_language"] = "False"
    valid_event["context"]["course_user_tags"] = {"foo": "1"}
    valid_event["context"]["user_id"] = 123

    invalid_event = copy.deepcopy(valid_event)
    invalid_event["host"] = 1  # not string
    invalid_event["context"]["course_user_tags"] = {"foo": 1}  # not string
    invalid_event["context"]["user_id"] = "123"  # not integer
    invalid_event_str = json.dumps(invalid_event)

    validator = Validator(ModelSelector(module="ralph.models.edx"))
    result = validator.validate(
        [invalid_event_str], ignore_errors=False, fail_on_unknown=True
    )
    assert json.loads(next(result)) == valid_event


@pytest.mark.parametrize(
    "event, models, expected",
    [
        (
            {"foo": 1},
            [Server, create_model("A", foo=(int, 1))],
            create_model("A", foo=(int, 1)),
        )
    ],
)
def test_models_validator_get_first_valid_model_with_match(event, models, expected):
    """Test that the `get_first_valid_model` method returns the expected model."""

    def dummy_get_models(event: dict):
        return models

    validator = Validator(ModelSelector(module="os"))
    validator.model_selector.get_models = dummy_get_models
    assert (
        validator.get_first_valid_model(event).model_dump()
        == expected(**event).model_dump()
    )


@pytest.mark.parametrize(
    "event, models, error",
    [({"foo": 1}, [Server, UIPageClose], "validation errors for UIPageClose")],
)
def test_models_validator_get_first_valid_model_without_match(event, models, error):
    """Test that the `get_first_valid_model` method raises an exception when no model
    matches the given event.
    """

    def dummy_get_models(event: dict):
        return models

    validator = Validator(ModelSelector(module="os"))
    validator.model_selector.get_models = dummy_get_models
    with pytest.raises(ValidationError, match=error):
        validator.get_first_valid_model(event)
