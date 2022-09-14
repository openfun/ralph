"""Tests for the problem interaction event models."""

import json

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

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(EdxProblemHintDemandhintDisplayed)
def test_models_edx_edx_problem_hint_demandhint_displayed_with_valid_statement(
    statement,
):
    """Tests that a `edx.problem.hint.demandhint_displayed` statement has the expected
    `event_type` and `page`.
    """

    assert statement.event_type == "edx.problem.hint.demandhint_displayed"
    assert statement.page == "x_module"


@custom_given(EdxProblemHintDemandhintDisplayed)
def test_models_edx_edx_problem_hint_demandhint_displayed_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.problem.hint.demandhint_displayed` statement the selector
    `get_model` method should return `EdxProblemHintDemandhintDisplayed` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is EdxProblemHintDemandhintDisplayed
    )


@custom_given(EdxProblemHintFeedbackDisplayed)
def test_models_edx_edx_problem_hint_feedback_displayed_with_valid_statement(statement):
    """Tests that a `edx.problem.hint.feedback_displayed` statement has the expected
    `event_type` and `page`.
    """

    assert statement.event_type == "edx.problem.hint.feedback_displayed"
    assert statement.page == "x_module"


@custom_given(EdxProblemHintFeedbackDisplayed)
def test_models_edx_edx_problem_hint_feedback_displayed_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.problem.hint.feedback_displayed` statement the selector
    `get_model` method should return `EdxProblemHintFeedbackDisplayed` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is EdxProblemHintFeedbackDisplayed
    )


@custom_given(UIProblemCheck)
def test_models_edx_ui_problem_check_with_valid_statement(statement):
    """Tests that a `problem_check` browser statement has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "problem_check"
    assert statement.name == "problem_check"


@custom_given(UIProblemCheck)
def test_models_edx_ui_problem_check_selector_with_valid_statement(statement):
    """Tests given a `problem_check` statement the selector `get_model`
    method should return `UIProblemCheck` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemCheck
    )


@custom_given(ProblemCheck)
def test_models_edx_problem_check_with_valid_statement(statement):
    """Tests that a `problem_check` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "problem_check"
    assert statement.page == "x_module"


@custom_given(ProblemCheck)
def test_models_edx_problem_check_selector_with_valid_statement(statement):
    """Tests given a `problem_check` statement the selector `get_model` method should
    return `ProblemCheck` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is ProblemCheck


@custom_given(ProblemCheckFail)
def test_models_edx_problem_check_fail_with_valid_statement(statement):
    """Tests that a `problem_check_fail` server statement has the expected `event_type`
    and `page`.
    """

    assert statement.event_type == "problem_check_fail"
    assert statement.page == "x_module"


@custom_given(ProblemCheckFail)
def test_models_edx_problem_check_fail_selector_with_valid_statement(statement):
    """Tests given a `problem_check_fail` statement the selector `get_model` method
    should return `ProblemCheckFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is ProblemCheckFail
    )


@custom_given(UIProblemGraded)
def test_models_edx_ui_problem_graded_with_valid_statement(statement):
    """Tests that a `problem_graded` browser statement has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "problem_graded"
    assert statement.name == "problem_graded"


@custom_given(UIProblemGraded)
def test_models_edx_ui_problem_graded_selector_with_valid_statement(statement):
    """
    Tests given a `problem_graded` statement the selector `get_model`
    method should return `ProblemGraded` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemGraded
    )


@custom_given(ProblemRescore)
def test_models_edx_problem_rescore_with_valid_statement(statement):
    """Tests that a `problem_rescore` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "problem_rescore"
    assert statement.page == "x_module"


@custom_given(ProblemRescore)
def test_models_edx_problem_rescore_selector_with_valid_statement(statement):
    """Tests given a `problem_rescore` statement the selector `get_model` method should
    return `ProblemRescore` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is ProblemRescore
    )


@custom_given(ProblemRescoreFail)
def test_models_edx_problem_rescore_fail_with_valid_statement(statement):
    """Tests that a `problem_rescore` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "problem_rescore_fail"
    assert statement.page == "x_module"


@custom_given(ProblemRescoreFail)
def test_models_edx_problem_rescore_fail_selector_with_valid_statement(statement):
    """
    Tests given a `problem_rescore_fail` statement the selector `get_model` method
    should return `ProblemRescoreFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is ProblemRescoreFail
    )


@custom_given(UIProblemReset)
def test_models_edx_ui_problem_reset_with_valid_statement(statement):
    """Tests that a `problem_reset` browser statement has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "problem_reset"
    assert statement.name == "problem_reset"


@custom_given(UIProblemReset)
def test_models_edx_ui_problem_reset_selector_with_valid_statement(statement):
    """Tests given a `problem_reset` statement the selector `get_model` method should
    return `ProblemReset` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemReset
    )


@custom_given(UIProblemSave)
def test_models_edx_ui_problem_save_with_valid_statement(statement):
    """Tests that a `problem_save` browser statement has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "problem_save"
    assert statement.name == "problem_save"


@custom_given(UIProblemSave)
def test_models_edx_ui_problem_save_selector_with_valid_statement(statement):
    """Tests given a `problem_save` statement the selector `get_model` method should
    return `ProblemSave` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemSave
    )


@custom_given(UIProblemShow)
def test_models_edx_ui_problem_show_with_valid_statement(statement):
    """Tests that a `problem_show` browser statement has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "problem_show"
    assert statement.name == "problem_show"


@custom_given(UIProblemShow)
def test_models_edx_ui_problem_show_selector_with_valid_statement(statement):
    """Tests given a `problem_show` statement the selector `get_model` method should
    return `ProblemShow` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemShow
    )


@custom_given(ResetProblem)
def test_models_edx_reset_problem_with_valid_statement(statement):
    """Tests that a `reset_problem` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "reset_problem"
    assert statement.page == "x_module"


@custom_given(ResetProblem)
def test_models_edx_reset_problem_selector_with_valid_statement(statement):
    """Tests given a `reset_problem` statement the selector `get_model` method should
    return `ResetProblem` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is ResetProblem


@custom_given(ResetProblemFail)
def test_models_edx_reset_problem_fail_with_valid_statement(statement):
    """Tests that a `reset_problem_fail` server statement has the expected `event_type`
    and `page`.
    """

    assert statement.event_type == "reset_problem_fail"
    assert statement.page == "x_module"


@custom_given(ResetProblemFail)
def test_models_edx_reset_problem_fail_selector_with_valid_statement(statement):
    """Tests given a `reset_problem_fail` statement the selector `get_model` method
    should return `ResetProblemFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is ResetProblemFail
    )


@custom_given(SaveProblemFail)
def test_models_edx_save_problem_fail_with_valid_statement(statement):
    """Tests that a `save_problem_fail` server statement has the expected `event_type`
    and `page`.
    """

    assert statement.event_type == "save_problem_fail"
    assert statement.page == "x_module"


@custom_given(SaveProblemFail)
def test_models_edx_save_problem_fail_selector_with_valid_statement(statement):
    """Tests given a `reset_problem_fail` statement the selector `get_model` method
    should return `SaveProblemFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is SaveProblemFail
    )


@custom_given(SaveProblemSuccess)
def test_models_edx_save_problem_success_with_valid_statement(statement):
    """Tests that a `save_problem_success` server statement has the expected
    `event_type` and `page`.
    """

    assert statement.event_type == "save_problem_success"
    assert statement.page == "x_module"


@custom_given(SaveProblemSuccess)
def test_models_edx_save_problem_success_selector_with_valid_statement(statement):
    """Tests given a `reset_problem_success` statement the selector `get_model` method
    should return `SaveProblemSuccess` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is SaveProblemSuccess
    )


@custom_given(ShowAnswer)
def test_models_edx_show_answer_with_valid_statement(statement):
    """Tests that a `showanswer` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "showanswer"
    assert statement.page == "x_module"


@custom_given(ShowAnswer)
def test_models_edx_show_answer_selector_with_valid_statement(statement):
    """Tests given a `show_answer` statement the selector `get_model` method should
    return `ShowAnswer` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is ShowAnswer
