"""Tests for open response assessment statement event fields"""

import pytest
from pydantic import ValidationError

from ralph.models.edx.open_response_assessment.fields.events import (
    ORASaveSubmissionEventField,
)


def test_models_edx_ora_save_submission_event_field_with_valid_values():
    """Tests that a valid `ORASaveSubmissionEventField` does not raise a
    `ValidationError`.
    """

    try:
        ORASaveSubmissionEventField(**{"saved_response": {"parts": []}})
        ORASaveSubmissionEventField(
            **{"saved_response": {"parts": [{"text": "any string"}]}}
        )
    except ValidationError:
        pytest.fail("Valid ORASaveSubmissionEventField should not raise exceptions")


@pytest.mark.parametrize(
    "fields,error",
    [
        ({}, "saved_response\n  field required"),
        ({"not_saved_response": ""}, "saved_response\n  field required"),
        ({"saved_response": ""}, "Invalid JSON"),
        ({"saved_response": {}}, "saved_response -> parts\n  field required"),
        ({"saved_response": {"parts": ""}}, "parts\n  value is not a valid list"),
        ({"saved_response": {"parts": [None]}}, "none is not an allowed value"),
        (
            {"saved_response": {"parts": [{"not_text": ""}]}},
            "unexpected value; permitted: 'text'",
        ),
        (
            {"saved_response": {"parts": [{"text": None}]}},
            "none is not an allowed value",
        ),
    ],
)
def test_models_edx_ora_save_submission_event_field_with_invalid_values(fields, error):
    """Tests that invalid `ORASaveSubmissionEventField` raises a `ValidationError`."""

    with pytest.raises(ValidationError, match=error):
        ORASaveSubmissionEventField(**fields)
