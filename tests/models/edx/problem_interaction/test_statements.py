"""Tests for the problem interaction event models"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.edx.problem_interaction.fields.events import (
    CorrectMap,
    EdxProblemHintDemandhintDisplayedEventField,
    EdxProblemHintFeedbackDisplayedEventField,
    ProblemCheckEventField,
    ProblemCheckFailEventField,
    ProblemRescoreEventField,
    ProblemRescoreFailEventField,
    ResetProblemEventField,
    ResetProblemFailEventField,
    SaveProblemFailEventField,
    SaveProblemSuccessEventField,
    ShowAnswerEventField,
    State,
    UIProblemResetEventField,
    UIProblemShowEventField,
)
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


@settings(max_examples=1)
@given(
    st.builds(
        EdxProblemHintDemandhintDisplayed,
        referer=provisional.urls(),
        event=st.builds(EdxProblemHintDemandhintDisplayedEventField),
    )
)
def test_models_edx_edx_problem_hint_demandhint_displayed_with_valid_statement(
    statement,
):
    """Tests that a `edx.problem.hint.demandhint_displayed` statement has the expected `event_type`
    and `page`.
    """

    assert statement.event_type == "edx.problem.hint.demandhint_displayed"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        EdxProblemHintDemandhintDisplayed,
        referer=provisional.urls(),
        event=st.builds(EdxProblemHintDemandhintDisplayedEventField),
    )
)
def test_models_edx_edx_problem_hint_demandhint_displayed_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.problem.hint.demandhint_displayed` statement the selector `get_model`
    method should return `EdxProblemHintDemandhintDisplayed` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is EdxProblemHintDemandhintDisplayed
    )


@settings(max_examples=1)
@given(
    st.builds(
        EdxProblemHintFeedbackDisplayed,
        referer=provisional.urls(),
        event=st.builds(EdxProblemHintFeedbackDisplayedEventField),
    )
)
def test_models_edx_edx_problem_hint_feedback_displayed_with_valid_statement(statement):
    """Tests that a `edx.problem.hint.feedback_displayed` statement has the expected `event_type`
    and `page`.
    """

    assert statement.event_type == "edx.problem.hint.feedback_displayed"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        EdxProblemHintFeedbackDisplayed,
        referer=provisional.urls(),
        event=st.builds(EdxProblemHintFeedbackDisplayedEventField),
    )
)
def test_models_edx_edx_problem_hint_feedback_displayed_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.problem.hint.feedback_displayed` statement the selector `get_model`
    method should return `EdxProblemHintFeedbackDisplayed` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is EdxProblemHintFeedbackDisplayed
    )


@settings(max_examples=1)
@given(
    st.builds(
        UIProblemCheck,
        referer=provisional.urls(),
        page=provisional.urls(),
    )
)
def test_models_edx_ui_problem_check_with_valid_statement(statement):
    """Tests that a `problem_check` browser statement has the expected `event_type` and `name`."""

    assert statement.event_type == "problem_check"
    assert statement.name == "problem_check"


@settings(max_examples=1)
@given(
    st.builds(
        UIProblemCheck,
        referer=provisional.urls(),
        page=provisional.urls(),
    )
)
def test_models_edx_ui_problem_check_selector_with_valid_statement(statement):
    """Tests given a `problem_check` statement the selector `get_model`
    method should return `UIProblemCheck` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemCheck
    )


@settings(max_examples=1)
@given(
    st.builds(
        ProblemCheck,
        referer=provisional.urls(),
        event=st.builds(
            ProblemCheckEventField,
            state=st.builds(State),
        ),
    )
)
def test_models_edx_problem_check_with_valid_statement(statement):
    """Tests that a `problem_check` server statement has the expected `event_type` and `page`."""

    assert statement.event_type == "problem_check"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ProblemCheck,
        referer=provisional.urls(),
        event=st.builds(
            ProblemCheckEventField,
            state=st.builds(State),
        ),
    )
)
def test_models_edx_problem_check_selector_with_valid_statement(statement):
    """Tests given a `problem_check` statement the selector `get_model`
    method should return `ProblemCheck` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is ProblemCheck


@settings(max_examples=1)
@given(
    st.builds(
        ProblemCheckFail,
        referer=provisional.urls(),
        event=st.builds(
            ProblemCheckFailEventField,
            state=st.builds(State),
        ),
    )
)
def test_models_edx_problem_check_fail_with_valid_statement(statement):
    """Tests that a `problem_check_fail` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "problem_check_fail"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ProblemCheckFail,
        referer=provisional.urls(),
        event=st.builds(
            ProblemCheckFailEventField,
            state=st.builds(State),
        ),
    )
)
def test_models_edx_problem_check_fail_selector_with_valid_statement(statement):
    """Tests given a `problem_check_fail` statement the selector `get_model` method should return
    `ProblemCheckFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is ProblemCheckFail
    )


@settings(max_examples=1)
@given(st.builds(UIProblemGraded, referer=provisional.urls(), page=provisional.urls()))
def test_models_edx_ui_problem_graded_with_valid_statement(statement):
    """Tests that a `problem_graded` browser statement has the expected `event_type` and `name`."""

    assert statement.event_type == "problem_graded"
    assert statement.name == "problem_graded"


@settings(max_examples=1)
@given(st.builds(UIProblemGraded, referer=provisional.urls(), page=provisional.urls()))
def test_models_edx_ui_problem_graded_selector_with_valid_statement(statement):
    """Tests given a `problem_graded` statement the selector `get_model`
    method should return `ProblemGraded` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemGraded
    )


@settings(max_examples=1)
@given(
    st.builds(
        ProblemRescore,
        referer=provisional.urls(),
        event=st.builds(
            ProblemRescoreEventField,
            state=st.builds(State),
            correct_map=st.builds(CorrectMap),
        ),
    )
)
def test_models_edx_problem_rescore_with_valid_statement(statement):
    """Tests that a `problem_rescore` server statement has the expected `event_type` and `page`."""

    assert statement.event_type == "problem_rescore"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ProblemRescore,
        referer=provisional.urls(),
        event=st.builds(
            ProblemRescoreEventField,
            state=st.builds(State),
            correct_map=st.builds(CorrectMap),
        ),
    )
)
def test_models_edx_problem_rescore_selector_with_valid_statement(statement):
    """Tests given a `problem_rescore` statement the selector `get_model`
    method should return `ProblemRescore` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is ProblemRescore
    )


@settings(max_examples=1)
@given(
    st.builds(
        ProblemRescoreFail,
        referer=provisional.urls(),
        event=st.builds(ProblemRescoreFailEventField, state=st.builds(State)),
    )
)
def test_models_edx_problem_rescore_fail_with_valid_statement(statement):
    """Tests that a `problem_rescore` server statement has the expected `event_type` and `page`."""

    assert statement.event_type == "problem_rescore_fail"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ProblemRescoreFail,
        referer=provisional.urls(),
        event=st.builds(ProblemRescoreFailEventField, state=st.builds(State)),
    )
)
def test_models_edx_problem_rescore_fail_selector_with_valid_statement(statement):
    """Tests given a `problem_rescore_fail` statement the selector `get_model`
    method should return `ProblemRescoreFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is ProblemRescoreFail
    )


@settings(max_examples=1)
@given(
    st.builds(
        UIProblemReset,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(UIProblemResetEventField),
    )
)
def test_models_edx_ui_problem_reset_with_valid_statement(statement):
    """Tests that a `problem_reset` browser statement has the expected `event_type` and `name`."""

    assert statement.event_type == "problem_reset"
    assert statement.name == "problem_reset"


@settings(max_examples=1)
@given(
    st.builds(
        UIProblemReset,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(UIProblemResetEventField),
    )
)
def test_models_edx_ui_problem_reset_selector_with_valid_statement(statement):
    """Tests given a `problem_reset` statement the selector `get_model`
    method should return `ProblemReset` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemReset
    )


@settings(max_examples=1)
@given(st.builds(UIProblemSave, referer=provisional.urls(), page=provisional.urls()))
def test_models_edx_ui_problem_save_with_valid_statement(statement):
    """Tests that a `problem_save` browser statement has the expected `event_type` and `name`."""

    assert statement.event_type == "problem_save"
    assert statement.name == "problem_save"


@settings(max_examples=1)
@given(st.builds(UIProblemSave, referer=provisional.urls(), page=provisional.urls()))
def test_models_edx_ui_problem_save_selector_with_valid_statement(statement):
    """Tests given a `problem_save` statement the selector `get_model`
    method should return `ProblemSave` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemSave
    )


@settings(max_examples=1)
@given(
    st.builds(
        UIProblemShow,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(UIProblemShowEventField),
    )
)
def test_models_edx_ui_problem_show_with_valid_statement(statement):
    """Tests that a `problem_show` browser statement has the expected `event_type` and `name`."""

    assert statement.event_type == "problem_show"
    assert statement.name == "problem_show"


@settings(max_examples=1)
@given(
    st.builds(
        UIProblemShow,
        referer=provisional.urls(),
        page=provisional.urls(),
        event=st.builds(UIProblemShowEventField),
    )
)
def test_models_edx_ui_problem_show_selector_with_valid_statement(statement):
    """Tests given a `problem_show` statement the selector `get_model`
    method should return `ProblemShow` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is UIProblemShow
    )


@settings(max_examples=1)
@given(
    st.builds(
        ResetProblem,
        referer=provisional.urls(),
        event=st.builds(
            ResetProblemEventField,
            old_state=st.builds(State),
            new_state=st.builds(State),
        ),
    )
)
def test_models_edx_reset_problem_with_valid_statement(statement):
    """Tests that a `reset_problem` server statement has the expected `event_type` and `page`."""

    assert statement.event_type == "reset_problem"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ResetProblem,
        referer=provisional.urls(),
        event=st.builds(
            ResetProblemEventField,
            old_state=st.builds(State),
            new_state=st.builds(State),
        ),
    )
)
def test_models_edx_reset_problem_selector_with_valid_statement(statement):
    """Tests given a `reset_problem` statement the selector `get_model`
    method should return `ResetProblem` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is ResetProblem


@settings(max_examples=1)
@given(
    st.builds(
        ResetProblemFail,
        referer=provisional.urls(),
        event=st.builds(ResetProblemFailEventField, old_state=st.builds(State)),
    )
)
def test_models_edx_reset_problem_fail_with_valid_statement(statement):
    """Tests that a `reset_problem_fail` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "reset_problem_fail"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ResetProblemFail,
        referer=provisional.urls(),
        event=st.builds(ResetProblemFailEventField, old_state=st.builds(State)),
    )
)
def test_models_edx_reset_problem_fail_selector_with_valid_statement(statement):
    """Tests given a `reset_problem_fail` statement the selector `get_model`
    method should return `ResetProblemFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is ResetProblemFail
    )


@settings(max_examples=1)
@given(
    st.builds(
        SaveProblemFail,
        referer=provisional.urls(),
        event=st.builds(SaveProblemFailEventField, state=st.builds(State)),
    )
)
def test_models_edx_save_problem_fail_with_valid_statement(statement):
    """Tests that a `save_problem_fail` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "save_problem_fail"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        SaveProblemFail,
        referer=provisional.urls(),
        event=st.builds(SaveProblemFailEventField, state=st.builds(State)),
    )
)
def test_models_edx_save_problem_fail_selector_with_valid_statement(statement):
    """Tests given a `reset_problem_fail` statement the selector `get_model`
    method should return `SaveProblemFail` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement) is SaveProblemFail
    )


@settings(max_examples=1)
@given(
    st.builds(
        SaveProblemSuccess,
        referer=provisional.urls(),
        event=st.builds(SaveProblemSuccessEventField, state=st.builds(State)),
    )
)
def test_models_edx_save_problem_success_with_valid_statement(statement):
    """Tests that a `save_problem_success` server statement has the expected `event_type` and
    `page`.
    """

    assert statement.event_type == "save_problem_success"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        SaveProblemSuccess,
        referer=provisional.urls(),
        event=st.builds(SaveProblemSuccessEventField, state=st.builds(State)),
    )
)
def test_models_edx_save_problem_success_selector_with_valid_statement(statement):
    """Tests given a `reset_problem_success` statement the selector `get_model`
    method should return `SaveProblemSuccess` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is SaveProblemSuccess
    )


@settings(max_examples=1)
@given(
    st.builds(
        ShowAnswer, referer=provisional.urls(), event=st.builds(ShowAnswerEventField)
    )
)
def test_models_edx_show_answer_with_valid_statement(statement):
    """Tests that a `showanswer` server statement has the expected `event_type` and `page`."""

    assert statement.event_type == "showanswer"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ShowAnswer, referer=provisional.urls(), event=st.builds(ShowAnswerEventField)
    )
)
def test_models_edx_show_answer_selector_with_valid_statement(statement):
    """Tests given a `show_answer` statement the selector `get_model`
    method should return `ShowAnswer` model.
    """

    statement = json.loads(statement.json())
    assert ModelSelector(module="ralph.models.edx").get_model(statement) is ShowAnswer
