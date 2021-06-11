"""Tests for the open response assessment event models"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.edx.open_response_assessment import (
    ORASaveSubmission,
    ORASaveSubmissionEventField,
    ORASaveSubmissionEventSavedResponseField,
)
from ralph.models.edx.x_block import ContextField
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(
    st.builds(
        ORASaveSubmission,
        context=st.builds(ContextField),
        referer=provisional.urls(),
        event=st.builds(
            ORASaveSubmissionEventField,
            saved_response=st.builds(ORASaveSubmissionEventSavedResponseField),
        ),
    )
)
def test_models_edx_ora_save_submission_with_valid_event(event):
    """Tests given an `openassessmentblock.save_submission` event the get_model method
    should return an ORASaveSubmission model.
    """

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event) is ORASaveSubmission
    )
