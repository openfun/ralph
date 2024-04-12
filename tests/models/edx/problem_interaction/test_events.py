"""Tests for problem interaction models event fields."""

import json
import re

import pytest
from pydantic import ValidationError

from ralph.models.edx.problem_interaction.fields.events import (
    CorrectMap,
    EdxProblemHintFeedbackDisplayedEventField,
    ProblemCheckEventField,
    ProblemCheckFailEventField,
    ProblemRescoreEventField,
    ProblemRescoreFailEventField,
    ResetProblemEventField,
    ResetProblemFailEventField,
    SaveProblemFailEventField,
    SaveProblemSuccessEventField,
)

from tests.factories import mock_instance


def test_models_edx_correct_map_with_valid_content():
    """Test that a valid `CorrectMap` does not raise a `ValidationError`."""
    subfield = mock_instance(CorrectMap)
    assert subfield.correctness in ("correct", "incorrect")
    assert subfield.hintmode in ("on_request", "always", None)


@pytest.mark.parametrize("correctness", ["corect", "incorect"])
def test_models_edx_correct_map_with_invalid_correctness_value(correctness):
    """Test that an invalid `correctness` value in `CorrectMap` raises a
    `ValidationError`.
    """
    subfield = mock_instance(CorrectMap)
    invalid_subfield = json.loads(subfield.model_dump_json())
    invalid_subfield["correctness"] = correctness

    with pytest.raises(
        ValidationError, match="correctness\n  Input should be 'correct' or 'incorrect'"
    ):
        CorrectMap(**invalid_subfield)


@pytest.mark.parametrize("hintmode", ["onrequest", "alway"])
def test_models_edx_correct_map_with_invalid_hintmode_value(hintmode):
    """Test that an invalid `hintmode` value in `CorrectMap` raises a
    `ValidationError`.
    """
    subfield = mock_instance(CorrectMap)
    invalid_subfield = json.loads(subfield.model_dump_json())
    invalid_subfield["hintmode"] = hintmode

    with pytest.raises(
        ValidationError, match="hintmode\n  Input should be 'on_request' or 'always'"
    ):
        CorrectMap(**invalid_subfield)


def test_models_edx_problem_hint_feedback_displayed_event_field_with_valid_field():
    """Test that a valid `EdxProblemHintFeedbackDisplayedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxProblemHintFeedbackDisplayedEventField)
    assert field.question_type in (
        "stringresponse",
        "choiceresponse",
        "multiplechoiceresponse",
        "numericalresponse",
        "optionresponse",
    )
    assert field.trigger_type in ("single", "compound")


@pytest.mark.parametrize(
    "question_type",
    [
        "stringrespons",
        "choicerespons",
        "multiplechoicerespons",
        "numericalrespons",
        "optionrespons",
    ],
)
def test_models_edx_problem_hint_feedback_displayed_event_field_with_invalid_question_type_value(  # noqa
    question_type,
):
    """Test that an invalid `question_type` value in
    `EdxProblemHintFeedbackDisplayedEventField` raises a `ValidationError`.
    """
    field = mock_instance(EdxProblemHintFeedbackDisplayedEventField)

    invalid_field = json.loads(field.model_dump_json())
    invalid_field["question_type"] = question_type

    with pytest.raises(
        ValidationError,
        match=(
            "question_type\n  Input should be 'stringresponse', 'choiceresponse', "
            "'multiplechoiceresponse', 'numericalresponse' or 'optionresponse'"
        ),
    ):
        EdxProblemHintFeedbackDisplayedEventField(**invalid_field)


@pytest.mark.parametrize("trigger_type", ["jingle", "compund"])
def test_models_edx_problem_hint_feedback_displayed_event_field_with_invalid_trigger_type_value(  # noqa
    trigger_type,
):
    """Test that an invalid `question_type` value in
    `EdxProblemHintFeedbackDisplayedEventField` raises a `ValidationError`.
    """
    field = mock_instance(EdxProblemHintFeedbackDisplayedEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["trigger_type"] = trigger_type

    with pytest.raises(
        ValidationError, match="trigger_type\n  Input should be 'single' or 'compound'"
    ):
        EdxProblemHintFeedbackDisplayedEventField(**invalid_field)


def test_models_edx_problem_check_event_field_with_valid_field():
    """Test that a valid `ProblemCheckEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ProblemCheckEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )
    assert field.success in ("correct", "incorrect")


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_problem_check_event_field_with_invalid_problem_id_value(problem_id):
    """Test that an invalid `problem_id` value in `ProblemCheckEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ProblemCheckEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        ProblemCheckEventField(**invalid_field)


@pytest.mark.parametrize("success", ["corect", "incorect"])
def test_models_edx_problem_check_event_field_with_invalid_success_value(success):
    """Test that an invalid `success` value in `ProblemCheckEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ProblemCheckEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["success"] = success

    with pytest.raises(
        ValidationError, match="success\n  Input should be 'correct' or 'incorrect'"
    ):
        ProblemCheckEventField(**invalid_field)


def test_models_edx_problem_check_fail_event_field_with_valid_field():
    """Test that a valid `ProblemCheckFailEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ProblemCheckFailEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )
    assert field.failure in ("closed", "unreset")


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_problem_check_fail_event_field_with_invalid_problem_id_value(
    problem_id,
):
    """Test that an invalid `problem_id` value in `ProblemCheckFailEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ProblemCheckFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        ProblemCheckFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "unresit"])
def test_models_edx_problem_check_fail_event_field_with_invalid_failure_value(failure):
    """Test that an invalid `failure` value in `ProblemCheckFailEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ProblemCheckFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["failure"] = failure

    with pytest.raises(
        ValidationError, match="failure\n  Input should be 'closed' or 'unreset'"
    ):
        ProblemCheckFailEventField(**invalid_field)


def test_models_edx_problem_rescore_event_field_with_valid_field():
    """Test that a valid `ProblemRescoreEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ProblemRescoreEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )
    assert field.success in ("correct", "incorrect")


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_problem_rescore_event_field_with_invalid_problem_id_value(
    problem_id,
):
    """Test that an invalid `problem_id` value in `ProblemRescoreEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ProblemRescoreEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        ProblemRescoreEventField(**invalid_field)


@pytest.mark.parametrize("success", ["corect", "incorect"])
def test_models_edx_problem_rescore_event_field_with_invalid_success_value(success):
    """Test that an invalid `success` value in `ProblemRescoreEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ProblemRescoreEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["success"] = success

    with pytest.raises(
        ValidationError, match="success\n  Input should be 'correct' or 'incorrect'"
    ):
        ProblemRescoreEventField(**invalid_field)


def test_models_edx_problem_rescore_fail_event_field_with_valid_field():
    """Test that a valid `ProblemRescoreFailEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ProblemRescoreFailEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )
    assert field.failure in ("closed", "unreset")


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_problem_rescore_fail_event_field_with_invalid_problem_id_value(
    problem_id,
):
    """Test that an invalid `problem_id` value in `ProblemRescoreFailEventField` raises
    a `ValidationError`.
    """
    field = mock_instance(ProblemRescoreFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        ProblemRescoreFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "unresit"])
def test_models_edx_problem_rescore_fail_event_field_with_invalid_failure_value(
    failure,
):
    """Test that an invalid `failure` value in `ProblemRescoreFailEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ProblemRescoreFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["failure"] = failure

    with pytest.raises(
        ValidationError, match="failure\n  Input should be 'closed' or 'unreset'"
    ):
        ProblemRescoreFailEventField(**invalid_field)


def test_models_edx_reset_problem_event_field_with_valid_field():
    """Test that a valid `ResetProblemEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ResetProblemEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_reset_problem_event_field_with_invalid_problem_id_value(problem_id):
    """Test that an invalid `problem_id` value in `ResetProblemEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ResetProblemEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        ResetProblemEventField(**invalid_field)


def test_models_edx_reset_problem_fail_event_field_with_valid_field():
    """Test that a valid `ResetProblemFailEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ResetProblemFailEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )
    assert field.failure in ("closed", "not_done")


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_reset_problem_fail_event_field_with_invalid_problem_id_value(
    problem_id,
):
    """Test that an invalid `problem_id` value in `ResetProblemFailEventField` raises
    a `ValidationError`.
    """
    field = mock_instance(ResetProblemFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        ResetProblemFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "not_close"])
def test_models_edx_reset_problem_fail_event_field_with_invalid_failure_value(failure):
    """Test that an invalid `failure` value in `ResetProblemFailEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ResetProblemFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["failure"] = failure

    with pytest.raises(
        ValidationError, match="failure\n  Input should be 'closed' or 'not_done'"
    ):
        ResetProblemFailEventField(**invalid_field)


def test_models_edx_save_problem_fail_event_field_with_valid_field():
    """Test that a valid `SaveProblemFailEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(SaveProblemFailEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )
    assert field.failure in ("closed", "done")


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_save_problem_fail_event_field_with_invalid_problem_id_value(
    problem_id,
):
    """Test that an invalid `problem_id` value in `SaveProblemFailEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(SaveProblemFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        SaveProblemFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "doned"])
def test_models_edx_save_problem_fail_event_field_with_invalid_failure_value(failure):
    """Test that an invalid `failure` value in `SaveProblemFailEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(SaveProblemFailEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["failure"] = failure

    with pytest.raises(
        ValidationError, match="failure\n  Input should be 'closed' or 'done'"
    ):
        SaveProblemFailEventField(**invalid_field)


def test_models_edx_save_problem_success_event_field_with_valid_field():
    """Test that a valid `SaveProblemFailEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(SaveProblemSuccessEventField)
    assert re.match(
        (
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]"
            r"+type@problem\+block@[a-f0-9]{32}$"
        ),
        field.problem_id,
    )


@pytest.mark.parametrize(
    "problem_id",
    [
        (
            "block-v2:orgX=CS111+20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS11120_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+tipe@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea1"
        ),
        "block-v1:orgX=CS111=20_T1+",
        "type@sequentialblock@d0d4a647742943e3951b45d9db8a0ea1",
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943z3951b45d9db8a0ea1"
        ),
        (
            "block-v1:orgX=CS111=20_T1+type@sequential"
            "+block@d0d4a647742943e3951b45d9db8a0ea13"
        ),
    ],
)
def test_models_edx_save_problem_success_event_field_with_invalid_problem_id_value(
    problem_id,
):
    """Test that an invalid `problem_id` value in `SaveProblemSuccessEventField`
    raises a `ValidationError`.
    """
    field = mock_instance(SaveProblemSuccessEventField)
    invalid_field = json.loads(field.model_dump_json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  String should match pattern"
    ):
        SaveProblemSuccessEventField(**invalid_field)
