"""Tests for open response assessment statement event fields."""

import json
import re

import pytest
from pydantic import ValidationError

from ralph.models.edx.open_response_assessment.fields.events import (
    ORAAssessEventField,
    ORAAssessEventRubricField,
    ORAGetPeerSubmissionEventField,
    ORAGetSubmissionForStaffGradingEventField,
)

# from tests.fixtures.hypothesis_strategies import custom_given
from tests.factories import mock_instance

def test_models_edx_ora_get_peer_submission_event_field_with_valid_values():
    """Test that a valid `ORAGetPeerSubmissionEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ORAGetPeerSubmissionEventField)

    assert re.match(
        r"^block-v1:.+\+.+\+.+type@openassessment+block@[a-f0-9]{32}$", field.item_id
    )


def test_models_edx_ora_get_submission_for_staff_grading_event_field_with_valid_values(
):
    """Test that a valid `ORAGetSubmissionForStaffGradingEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ORAGetSubmissionForStaffGradingEventField)

    assert re.match(
        r"^block-v1:.+\+.+\+.+type@openassessment+block@[a-f0-9]{32}$", field.item_id
    )


def test_models_edx_ora_assess_event_field_with_valid_values():
    """Test that a valid `ORAAssessEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(ORAAssessEventField)

    assert field.score_type in {"PE", "SE", "ST"}


@pytest.mark.parametrize(
    "score_type",
    ["pe", "se", "st", "SA", "PA", "22", "&T"],
)
def test_models_edx_ora_assess_event_field_with_invalid_values(score_type):
    """Test that invalid `ORAAssessEventField` raises a `ValidationError`."""
    field = mock_instance(ORAAssessEventField)

    invalid_field = json.loads(field.json())
    invalid_field["score_type"] = score_type

    with pytest.raises(ValidationError, match="score_type\n  unexpected value"):
        ORAAssessEventField(**invalid_field)


@pytest.mark.parametrize(
    "content_hash",
    [
        "d0d4a647742943e3951b45d9db8a0ea1ff71ae3&",
        "d0d4a647742943e3951b45d9db8a0ea1ff71ae360",
        "D0d4a647742943e3951b45d9db8a0ea1ff71ae36",
    ],
)
def test_models_edx_ora_assess_event_rubric_field_with_invalid_problem_id_value(
    content_hash
):
    """Test that an invalid `problem_id` value in `ProblemCheckEventField` raises a
    `ValidationError`.
    """
    field = mock_instance(ORAAssessEventRubricField)

    invalid_field = json.loads(field.json())
    invalid_field["content_hash"] = content_hash

    with pytest.raises(
        ValidationError, match="content_hash\n  string does not match regex"
    ):
        ORAAssessEventRubricField(**invalid_field)
