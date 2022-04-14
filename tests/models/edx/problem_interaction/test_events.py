"""Tests for problem interaction models event fields"""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

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

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(CorrectMap)
def test_models_edx_correct_map_with_valid_content(subfield):
    """Tests that a valid `CorrectMap` does not raise a `ValidationError`."""

    assert subfield.correctness in ("correct", "incorrect")
    assert subfield.hintmode in ("on_request", "always", None)


@pytest.mark.parametrize("correctness", ["corect", "incorect"])
@custom_given(CorrectMap)
def test_models_edx_correct_map_with_invalid_correctness_value(correctness, subfield):
    """Tests that an invalid `correctness` value in `CorrectMap` raises a
    `ValidationError`.
    """

    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["correctness"] = correctness

    with pytest.raises(ValidationError, match="correctness\n  unexpected value"):
        CorrectMap(**invalid_subfield)


@pytest.mark.parametrize("hintmode", ["onrequest", "alway"])
@custom_given(CorrectMap)
def test_models_edx_correct_map_with_invalid_hintmode_value(hintmode, subfield):
    """Tests that an invalid `hintmode` value in `CorrectMap` raises a
    `ValidationError`.
    """

    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["hintmode"] = hintmode

    with pytest.raises(ValidationError, match="hintmode\n  unexpected value"):
        CorrectMap(**invalid_subfield)


@custom_given(EdxProblemHintFeedbackDisplayedEventField)
def test_models_edx_problem_hint_feedback_displayed_event_field_with_valid_field(field):
    """Tests that a valid `EdxProblemHintFeedbackDisplayedEventField` does not raise a
    `ValidationError`.
    """

    assert field.question_type in (
        "stringresponse",
        "choiceresponse",
        "multiplechoiceresponse",
        "numericalresponse",
        "optionresponse",
    )
    assert field.trigger_type in ("single", "compound")


# pylint: disable=line-too-long
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
@custom_given(EdxProblemHintFeedbackDisplayedEventField)
def test_models_edx_problem_hint_feedback_displayed_event_field_with_invalid_question_type_value(  # noqa
    question_type, field
):
    """Tests that an invalid `question_type` value in
    `EdxProblemHintFeedbackDisplayedEventField` raises a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["question_type"] = question_type

    with pytest.raises(ValidationError, match="question_type\n  unexpected value"):
        EdxProblemHintFeedbackDisplayedEventField(**invalid_field)


# pylint: disable=line-too-long
@pytest.mark.parametrize("trigger_type", ["jingle", "compund"])
@custom_given(EdxProblemHintFeedbackDisplayedEventField)
def test_models_edx_problem_hint_feedback_displayed_event_field_with_invalid_trigger_type_value(  # noqa
    trigger_type, field
):
    """Tests that an invalid `question_type` value in
    `EdxProblemHintFeedbackDisplayedEventField` raises a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["trigger_type"] = trigger_type

    with pytest.raises(ValidationError, match="trigger_type\n  unexpected value"):
        EdxProblemHintFeedbackDisplayedEventField(**invalid_field)


@custom_given(ProblemCheckEventField)
def test_models_edx_problem_check_event_field_with_valid_field(field):
    """Tests that a valid `ProblemCheckEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(ProblemCheckEventField)
def test_models_edx_problem_check_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `ProblemCheckEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        ProblemCheckEventField(**invalid_field)


@pytest.mark.parametrize("success", ["corect", "incorect"])
@custom_given(ProblemCheckEventField)
def test_models_edx_problem_check_event_field_with_invalid_success_value(
    success, field
):
    """Tests that an invalid `success` value in `ProblemCheckEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["success"] = success

    with pytest.raises(ValidationError, match="success\n  unexpected value"):
        ProblemCheckEventField(**invalid_field)


@custom_given(ProblemCheckFailEventField)
def test_models_edx_problem_check_fail_event_field_with_valid_field(field):
    """Tests that a valid `ProblemCheckFailEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(ProblemCheckFailEventField)
def test_models_edx_problem_check_fail_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `ProblemCheckFailEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        ProblemCheckFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "unresit"])
@custom_given(ProblemCheckFailEventField)
def test_models_edx_problem_check_fail_event_field_with_invalid_failure_value(
    failure, field
):
    """Tests that an invalid `failure` value in `ProblemCheckFailEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["failure"] = failure

    with pytest.raises(ValidationError, match="failure\n  unexpected value"):
        ProblemCheckFailEventField(**invalid_field)


@custom_given(ProblemRescoreEventField)
def test_models_edx_problem_rescore_event_field_with_valid_field(field):
    """Tests that a valid `ProblemRescoreEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(ProblemRescoreEventField)
def test_models_edx_problem_rescore_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `ProblemRescoreEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        ProblemRescoreEventField(**invalid_field)


@pytest.mark.parametrize("success", ["corect", "incorect"])
@custom_given(ProblemRescoreEventField)
def test_models_edx_problem_rescore_event_field_with_invalid_success_value(
    success, field
):
    """Tests that an invalid `success` value in `ProblemRescoreEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["success"] = success

    with pytest.raises(ValidationError, match="success\n  unexpected value"):
        ProblemRescoreEventField(**invalid_field)


@custom_given(ProblemRescoreFailEventField)
def test_models_edx_problem_rescore_fail_event_field_with_valid_field(field):
    """Tests that a valid `ProblemRescoreFailEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(ProblemRescoreFailEventField)
def test_models_edx_problem_rescore_fail_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `ProblemRescoreFailEventField` raises
    a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        ProblemRescoreFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "unresit"])
@custom_given(ProblemRescoreFailEventField)
def test_models_edx_problem_rescore_fail_event_field_with_invalid_failure_value(
    failure, field
):
    """Tests that an invalid `failure` value in `ProblemRescoreFailEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["failure"] = failure

    with pytest.raises(ValidationError, match="failure\n  unexpected value"):
        ProblemRescoreFailEventField(**invalid_field)


@custom_given(ResetProblemEventField)
def test_models_edx_reset_problem_event_field_with_valid_field(field):
    """Tests that a valid `ResetProblemEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(ResetProblemEventField)
def test_models_edx_reset_problem_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `ResetProblemEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        ResetProblemEventField(**invalid_field)


@custom_given(ResetProblemFailEventField)
def test_models_edx_reset_problem_fail_event_field_with_valid_field(field):
    """Tests that a valid `ResetProblemFailEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(ResetProblemFailEventField)
def test_models_edx_reset_problem_fail_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `ResetProblemFailEventField` raises
    a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        ResetProblemFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "not_close"])
@custom_given(ResetProblemFailEventField)
def test_models_edx_reset_problem_fail_event_field_with_invalid_failure_value(
    failure, field
):
    """Tests that an invalid `failure` value in `ResetProblemFailEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["failure"] = failure

    with pytest.raises(ValidationError, match="failure\n  unexpected value"):
        ResetProblemFailEventField(**invalid_field)


@custom_given(SaveProblemFailEventField)
def test_models_edx_save_problem_fail_event_field_with_valid_field(field):
    """Tests that a valid `SaveProblemFailEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(SaveProblemFailEventField)
def test_models_edx_save_problem_fail_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `SaveProblemFailEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        SaveProblemFailEventField(**invalid_field)


@pytest.mark.parametrize("failure", ["close", "doned"])
@custom_given(SaveProblemFailEventField)
def test_models_edx_save_problem_fail_event_field_with_invalid_failure_value(
    failure, field
):
    """Tests that an invalid `failure` value in `SaveProblemFailEventField` raises a
    `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["failure"] = failure

    with pytest.raises(ValidationError, match="failure\n  unexpected value"):
        SaveProblemFailEventField(**invalid_field)


@custom_given(SaveProblemSuccessEventField)
def test_models_edx_save_problem_success_event_field_with_valid_field(field):
    """Tests that a valid `SaveProblemFailEventField` does not raise a
    `ValidationError`.
    """

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
@custom_given(SaveProblemSuccessEventField)
def test_models_edx_save_problem_success_event_field_with_invalid_problem_id_value(
    problem_id, field
):
    """Tests that an invalid `problem_id` value in `SaveProblemSuccessEventField`
    raises a `ValidationError`.
    """

    invalid_field = json.loads(field.json())
    invalid_field["problem_id"] = problem_id

    with pytest.raises(
        ValidationError, match="problem_id\n  string does not match regex"
    ):
        SaveProblemSuccessEventField(**invalid_field)
