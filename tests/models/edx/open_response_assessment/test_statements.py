"""Tests for the open response assessment statement models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.open_response_assessment.statements import (
    ORACreateSubmission,
    ORAGetPeerSubmission,
    ORAGetSubmissionForStaffGrading,
    ORAPeerAssess,
    ORASaveSubmission,
    ORASelfAssess,
    ORAStaffAssess,
    ORAStudentTrainingAssessExample,
    ORASubmitFeedbackOnAssessments,
    ORAUploadFile,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "class_",
    [
        ORASaveSubmission,
        ORACreateSubmission,
        ORAStaffAssess,
        ORAPeerAssess,
        ORASelfAssess,
        ORAGetPeerSubmission,
        ORAGetSubmissionForStaffGrading,
        ORAUploadFile,
        ORASubmitFeedbackOnAssessments,
        ORAStudentTrainingAssessExample,
    ],
)
@custom_given(st.data())
def test_models_edx_ora_selectors_with_valid_statements(class_, data):
    """Test given a valid open response assessment edX statement the `get_first_model`
    selector method should return the expected model.
    """

    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(ORAGetPeerSubmission)
def test_models_edx_ora_get_peer_submission_with_valid_statement(statement):
    """Test that a `openassessmentblock.get_peer_submission` statement has the expected
    `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.get_peer_submission"
    assert statement.page == "x_module"


@custom_given(ORAGetSubmissionForStaffGrading)
def test_models_edx_ora_get_submission_for_staff_grading_with_valid_statement(
    statement,
):
    """Test that a `openassessmentblock.get_submission_for_staff_grading` statement has
    the expected `event_type` and `page` fields.
    """

    assert (
        statement.event_type == "openassessmentblock.get_submission_for_staff_grading"
    )
    assert statement.page == "x_module"


@custom_given(ORAPeerAssess)
def test_models_edx_ora_peer_assess_with_valid_statement(statement):
    """Test that a `openassessmentblock.peer_assess` statement has the expected
    `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.peer_assess"
    assert statement.page == "x_module"


@custom_given(ORASelfAssess)
def test_models_edx_ora_self_assess_with_valid_statement(statement):
    """Test that a `openassessmentblock.self_assess` statement has the expected
    `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.self_assess"
    assert statement.page == "x_module"


@custom_given(ORAStaffAssess)
def test_models_edx_ora_staff_assess_with_valid_statement(statement):
    """Test that a `openassessmentblock.staff_assess` statement has the expected
    `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.staff_assess"
    assert statement.page == "x_module"


@custom_given(ORASubmitFeedbackOnAssessments)
def test_models_edx_ora_submit_feedback_on_assessments_with_valid_statement(statement):
    """Test that a `openassessmentblock.submit_feedback_on_assessments` statement has
    the expected `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.submit_feedback_on_assessments"
    assert statement.page == "x_module"


@custom_given(ORACreateSubmission)
def test_models_edx_ora_create_submission_with_valid_statement(statement):
    """Test that a `openassessmentblock.create_submission` statement has the expected
    `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.create_submission"
    assert statement.page == "x_module"


@custom_given(ORASaveSubmission)
def test_models_edx_ora_save_submission_with_valid_statement(statement):
    """Test that a `openassessmentblock.save_submission` statement has the expected
    `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessmentblock.save_submission"
    assert statement.page == "x_module"


@custom_given(ORAStudentTrainingAssessExample)
def test_models_edx_ora_student_training_assess_example_with_valid_statement(statement):
    """Test that a `openassessment.student_training_assess_example` statement
    has the expected `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessment.student_training_assess_example"
    assert statement.page == "x_module"


@custom_given(ORAUploadFile)
def test_models_edx_ora_upload_file_example_with_valid_statement(statement):
    """Test that a `openassessment.upload_file` statement
    has the expected `event_type` and `page` fields.
    """

    assert statement.event_type == "openassessment.upload_file"
    assert statement.name == "openassessment.upload_file"
