"""Tests for the `video` xAPI profile."""

import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st

from ralph.models.selector import ModelSelector
from ralph.models.xapi.quiz.statements import (
    QuizCompleted,
    QuizFailed,
    QuizInitialized,
    QuizLaunched,
    QuizPassed,
    QuizTerminated,
)

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@settings(deadline=None)
@pytest.mark.parametrize(
    "class_",
    [
        QuizTerminated,
        QuizCompleted,
        QuizFailed,
        QuizInitialized,
        QuizLaunched,
        QuizPassed,
    ],
)
@custom_given(st.data())
def test_models_xapi_quiz_selectors_with_valid_statements(class_, data):
    """Tests given a valid quiz xAPI statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.xapi").get_first_model(statement)
    assert model is class_


@custom_given(QuizInitialized)
def test_models_xapi_quiz_initialized_with_valid_statement(statement):
    """Tests that a valid quiz initialized statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/initialized"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )


@custom_given(QuizLaunched)
def test_models_xapi_quiz_launched_with_valid_statement(statement):
    """Tests that a valid quiz launched statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/launched"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )


@custom_given(QuizFailed)
def test_models_xapi_quiz_failed_with_valid_statement(statement):
    """Tests that a valid quiz failed statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/failed"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )


@custom_given(QuizPassed)
def test_models_xapi_quiz_passed_with_valid_statement(statement):
    """Tests that a valid quiz passed statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values."""

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/passed"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )


@custom_given(QuizCompleted)
def test_models_xapi_quiz_completed_with_valid_statement(statement):
    """Tests that a valid quiz completed statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/completed"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )


@custom_given(QuizTerminated)
def test_models_xapi_quiz_terminated_with_valid_statement(statement):
    """Tests that a valid quiz terminated statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """

    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert (
        statement.object.definition.type
        == "http://adlnet.gov/expapi/activities/cmi.interaction"
    )
