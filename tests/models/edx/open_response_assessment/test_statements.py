"""Tests for the open response assessment statement models"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.edx.base import BaseContextField
from ralph.models.edx.open_response_assessment.fields.events import (
    ORASaveSubmissionEventField,
    ORASaveSubmissionEventSavedResponseField,
)
from ralph.models.edx.open_response_assessment.statements import ORASaveSubmission
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(
    st.builds(
        ORASaveSubmission,
        context=st.builds(BaseContextField),
        referer=provisional.urls(),
        event=st.builds(
            ORASaveSubmissionEventField,
            saved_response=st.builds(ORASaveSubmissionEventSavedResponseField),
        ),
    )
)
def test_models_edx_ora_save_submission_with_valid_statement(statement):
    """Tests that a `openassessmentblock.save_submission` statement has the expected
    `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.save_submission"
    assert statement.page == "x_module"


@settings(max_examples=1)
@given(
    st.builds(
        ORASaveSubmission,
        context=st.builds(BaseContextField),
        referer=provisional.urls(),
        event=st.builds(
            ORASaveSubmissionEventField,
            saved_response=st.builds(ORASaveSubmissionEventSavedResponseField),
        ),
    )
)
def test_models_edx_ora_save_submission_selector_with_valid_statement(statement):
    """Tests given an `openassessmentblock.save_submission` statement the selector
    `get_model` method should return an `ORASaveSubmission` model.
    """

    statement = json.loads(statement.json())
    model = ModelSelector(module="ralph.models.edx").get_model(statement)
    assert model is ORASaveSubmission
