"""Tests for the problem interaction event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.problem_interaction.statements import (
    EdxProblemHintDemandhintDisplayed,
    EdxProblemHintFeedbackDisplayed,
    ProblemCheck,
    ProblemCheckFail,
    ProblemRescore,
    ProblemRescoreFail,
    ResetProblem,
    ResetProblemFail,
    SaveProblemFail,
    SaveProblemSuccess,
    ShowAnswer,
    UIProblemCheck,
    UIProblemGraded,
    UIProblemReset,
    UIProblemSave,
    UIProblemShow,
)
from ralph.models.selector import ModelSelector

# from tests.fixtures.hypothesis_strategies import custom_builds, custom_given
from tests.factories import mock_instance

@pytest.mark.parametrize(
    "class_",
    [
        EdxProblemHintDemandhintDisplayed,
        EdxProblemHintFeedbackDisplayed,
        ProblemCheck,
        ProblemCheckFail,
        ProblemRescore,
        ProblemRescoreFail,
        ResetProblem,
        ResetProblemFail,
        SaveProblemFail,
        SaveProblemSuccess,
        ShowAnswer,
        UIProblemCheck,
        UIProblemGraded,
        UIProblemReset,
        UIProblemSave,
        UIProblemShow,
    ],
)
def test_models_edx_edx_problem_interaction_selectors_with_valid_statements(
    class_
):
    """Test given a valid problem interaction edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_problem_hint_demandhint_displayed_with_valid_statement(
):
    """Test that a `edx.problem.hint.demandhint_displayed` statement has the expected
    `event_type` and `page`.
    """
    statement = mock_instance(EdxProblemHintDemandhintDisplayed)
    assert statement.event_type == "edx.problem.hint.demandhint_displayed"
    assert statement.page == "x_module"


def test_models_edx_edx_problem_hint_feedback_displayed_with_valid_statement():
    """Test that a `edx.problem.hint.feedback_displayed` statement has the expected
    `event_type` and `page`.
    """
    statement = mock_instance(EdxProblemHintFeedbackDisplayed)
    assert statement.event_type == "edx.problem.hint.feedback_displayed"
    assert statement.page == "x_module"


def test_models_edx_ui_problem_check_with_valid_statement():
    """Test that a `problem_check` browser statement has the expected `event_type` and
    `name`.
    """
    statement = mock_instance(UIProblemCheck)
    assert statement.event_type == "problem_check"
    assert statement.name == "problem_check"


def test_models_edx_problem_check_with_valid_statement():
    """Test that a `problem_check` server statement has the expected `event_type` and
    `page`.
    """
    statement = mock_instance(ProblemCheck)
    assert statement.event_type == "problem_check"
    assert statement.page == "x_module"


def test_models_edx_problem_check_fail_with_valid_statement():
    """Test that a `problem_check_fail` server statement has the expected `event_type`
    and `page`.
    """
    statement = mock_instance(ProblemCheckFail)
    assert statement.event_type == "problem_check_fail"
    assert statement.page == "x_module"


def test_models_edx_ui_problem_graded_with_valid_statement():
    """Test that a `problem_graded` browser statement has the expected `event_type` and
    `name`.
    """
    statement = mock_instance(UIProblemGraded)
    assert statement.event_type == "problem_graded"
    assert statement.name == "problem_graded"


def test_models_edx_problem_rescore_with_valid_statement():
    """Test that a `problem_rescore` server statement has the expected `event_type` and
    `page`.
    """
    statement = mock_instance(ProblemRescore)
    assert statement.event_type == "problem_rescore"
    assert statement.page == "x_module"


def test_models_edx_problem_rescore_fail_with_valid_statement():
    """Test that a `problem_rescore` server statement has the expected `event_type` and
    `page`.
    """
    statement = mock_instance(ProblemRescoreFail)
    assert statement.event_type == "problem_rescore_fail"
    assert statement.page == "x_module"


def test_models_edx_ui_problem_reset_with_valid_statement():
    """Test that a `problem_reset` browser statement has the expected `event_type` and
    `name`.
    """
    statement = mock_instance(UIProblemReset)
    assert statement.event_type == "problem_reset"
    assert statement.name == "problem_reset"


def test_models_edx_ui_problem_save_with_valid_statement():
    """Test that a `problem_save` browser statement has the expected `event_type` and
    `name`.
    """
    statement = mock_instance(UIProblemSave)
    assert statement.event_type == "problem_save"
    assert statement.name == "problem_save"


def test_models_edx_ui_problem_show_with_valid_statement():
    """Test that a `problem_show` browser statement has the expected `event_type` and
    `name`.
    """
    statement = mock_instance(UIProblemShow)
    assert statement.event_type == "problem_show"
    assert statement.name == "problem_show"


def test_models_edx_reset_problem_with_valid_statement():
    """Test that a `reset_problem` server statement has the expected `event_type` and
    `page`.
    """
    statement = mock_instance(ResetProblem)
    assert statement.event_type == "reset_problem"
    assert statement.page == "x_module"


def test_models_edx_reset_problem_fail_with_valid_statement():
    """Test that a `reset_problem_fail` server statement has the expected `event_type`
    and `page`.
    """
    statement = mock_instance(ResetProblemFail)
    assert statement.event_type == "reset_problem_fail"
    assert statement.page == "x_module"


def test_models_edx_save_problem_fail_with_valid_statement():
    """Test that a `save_problem_fail` server statement has the expected `event_type`
    and `page`.
    """
    statement = mock_instance(SaveProblemFail)
    assert statement.event_type == "save_problem_fail"
    assert statement.page == "x_module"


def test_models_edx_save_problem_success_with_valid_statement():
    """Test that a `save_problem_success` server statement has the expected
    `event_type` and `page`.
    """
    statement = mock_instance(SaveProblemSuccess)
    assert statement.event_type == "save_problem_success"
    assert statement.page == "x_module"


def test_models_edx_show_answer_with_valid_statement():
    """Test that a `showanswer` server statement has the expected `event_type` and
    `page`.
    """
    statement = mock_instance(ShowAnswer)
    assert statement.event_type == "showanswer"
    assert statement.page == "x_module"
