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

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


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
@custom_given(st.data())
def test_models_edx_edx_problem_interaction_selectors_with_valid_statements(
    class_, data
):
    """Tests given a valid problem interaction edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(EdxProblemHintDemandhintDisplayed)
def test_models_edx_edx_problem_hint_demandhint_displayed_with_valid_statement(
    statement,
):
    """Tests that a `edx.problem.hint.demandhint_displayed` statement has the expected
    `event_type` and `page`.
    """
    assert statement.event_type == "edx.problem.hint.demandhint_displayed"
    assert statement.page == "x_module"


@custom_given(EdxProblemHintFeedbackDisplayed)
def test_models_edx_edx_problem_hint_feedback_displayed_with_valid_statement(statement):
    """Tests that a `edx.problem.hint.feedback_displayed` statement has the expected
    `event_type` and `page`.
    """
    assert statement.event_type == "edx.problem.hint.feedback_displayed"
    assert statement.page == "x_module"


@custom_given(UIProblemCheck)
def test_models_edx_ui_problem_check_with_valid_statement(statement):
    """Tests that a `problem_check` browser statement has the expected `event_type` and
    `name`.
    """
    assert statement.event_type == "problem_check"
    assert statement.name == "problem_check"


@custom_given(ProblemCheck)
def test_models_edx_problem_check_with_valid_statement(statement):
    """Tests that a `problem_check` server statement has the expected `event_type` and
    `page`.
    """
    assert statement.event_type == "problem_check"
    assert statement.page == "x_module"


@custom_given(ProblemCheckFail)
def test_models_edx_problem_check_fail_with_valid_statement(statement):
    """Tests that a `problem_check_fail` server statement has the expected `event_type`
    and `page`.
    """
    assert statement.event_type == "problem_check_fail"
    assert statement.page == "x_module"


@custom_given(UIProblemGraded)
def test_models_edx_ui_problem_graded_with_valid_statement(statement):
    """Tests that a `problem_graded` browser statement has the expected `event_type` and
    `name`.
    """
    assert statement.event_type == "problem_graded"
    assert statement.name == "problem_graded"


@custom_given(ProblemRescore)
def test_models_edx_problem_rescore_with_valid_statement(statement):
    """Tests that a `problem_rescore` server statement has the expected `event_type` and
    `page`.
    """
    assert statement.event_type == "problem_rescore"
    assert statement.page == "x_module"


@custom_given(ProblemRescoreFail)
def test_models_edx_problem_rescore_fail_with_valid_statement(statement):
    """Tests that a `problem_rescore` server statement has the expected `event_type` and
    `page`.
    """
    assert statement.event_type == "problem_rescore_fail"
    assert statement.page == "x_module"


@custom_given(UIProblemReset)
def test_models_edx_ui_problem_reset_with_valid_statement(statement):
    """Tests that a `problem_reset` browser statement has the expected `event_type` and
    `name`.
    """
    assert statement.event_type == "problem_reset"
    assert statement.name == "problem_reset"


@custom_given(UIProblemSave)
def test_models_edx_ui_problem_save_with_valid_statement(statement):
    """Tests that a `problem_save` browser statement has the expected `event_type` and
    `name`.
    """
    assert statement.event_type == "problem_save"
    assert statement.name == "problem_save"


@custom_given(UIProblemShow)
def test_models_edx_ui_problem_show_with_valid_statement(statement):
    """Tests that a `problem_show` browser statement has the expected `event_type` and
    `name`.
    """
    assert statement.event_type == "problem_show"
    assert statement.name == "problem_show"


@custom_given(ResetProblem)
def test_models_edx_reset_problem_with_valid_statement(statement):
    """Tests that a `reset_problem` server statement has the expected `event_type` and
    `page`.
    """
    assert statement.event_type == "reset_problem"
    assert statement.page == "x_module"


@custom_given(ResetProblemFail)
def test_models_edx_reset_problem_fail_with_valid_statement(statement):
    """Tests that a `reset_problem_fail` server statement has the expected `event_type`
    and `page`.
    """
    assert statement.event_type == "reset_problem_fail"
    assert statement.page == "x_module"


@custom_given(SaveProblemFail)
def test_models_edx_save_problem_fail_with_valid_statement(statement):
    """Tests that a `save_problem_fail` server statement has the expected `event_type`
    and `page`.
    """
    assert statement.event_type == "save_problem_fail"
    assert statement.page == "x_module"


@custom_given(SaveProblemSuccess)
def test_models_edx_save_problem_success_with_valid_statement(statement):
    """Tests that a `save_problem_success` server statement has the expected
    `event_type` and `page`.
    """
    assert statement.event_type == "save_problem_success"
    assert statement.page == "x_module"


@custom_given(ShowAnswer)
def test_models_edx_show_answer_with_valid_statement(statement):
    """Tests that a `showanswer` server statement has the expected `event_type` and
    `page`.
    """
    assert statement.event_type == "showanswer"
    assert statement.page == "x_module"
