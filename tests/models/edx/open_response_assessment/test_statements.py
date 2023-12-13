"""Tests for the open response assessment statement models."""

import json

import pytest

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

from tests.factories import mock_instance


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
def test_models_edx_ora_selectors_with_valid_statements(class_):
    """Test given a valid open response assessment edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_ora_get_peer_submission_with_valid_statement():
    """Test that a `openassessmentblock.get_peer_submission` statement has the expected
    `event_type` and `page` fields.
    """
    statement = mock_instance(ORAGetPeerSubmission)

    assert statement.event_type == "openassessmentblock.get_peer_submission"
    assert statement.page == "x_module"


def test_models_edx_ora_get_submission_for_staff_grading_with_valid_statement():
    """Test that a `openassessmentblock.get_submission_for_staff_grading` statement has
    the expected `event_type` and `page` fields.
    """
    statement = mock_instance(ORAGetSubmissionForStaffGrading)

    assert (
        statement.event_type == "openassessmentblock.get_submission_for_staff_grading"
    )
    assert statement.page == "x_module"


def test_models_edx_ora_peer_assess_with_valid_statement():
    """Test that a `openassessmentblock.peer_assess` statement has the expected
    `event_type` and `page` fields.
    """
    statement = mock_instance(ORAPeerAssess)

    assert statement.event_type == "openassessmentblock.peer_assess"
    assert statement.page == "x_module"


def test_models_edx_ora_self_assess_with_valid_statement():
    """Test that a `openassessmentblock.self_assess` statement has the expected
    `event_type` and `page` fields.
    """
    statement = mock_instance(ORASelfAssess)

    assert statement.event_type == "openassessmentblock.self_assess"
    assert statement.page == "x_module"


def test_models_edx_ora_staff_assess_with_valid_statement():
    """Test that a `openassessmentblock.staff_assess` statement has the expected
    `event_type` and `page` fields.
    """
    statement = mock_instance(ORAStaffAssess)

    assert statement.event_type == "openassessmentblock.staff_assess"
    assert statement.page == "x_module"


def test_models_edx_ora_submit_feedback_on_assessments_with_valid_statement():
    """Test that a `openassessmentblock.submit_feedback_on_assessments` statement has
    the expected `event_type` and `page` fields.
    """
    statement = mock_instance(ORASubmitFeedbackOnAssessments)

    assert statement.event_type == "openassessmentblock.submit_feedback_on_assessments"
    assert statement.page == "x_module"


def test_models_edx_ora_create_submission_with_valid_statement():
    """Test that a `openassessmentblock.create_submission` statement has the expected
    `event_type` and `page` fields.
    """
    statement = mock_instance(ORACreateSubmission)

    assert statement.event_type == "openassessmentblock.create_submission"
    assert statement.page == "x_module"


def test_models_edx_ora_save_submission_with_valid_statement():
    """Test that a `openassessmentblock.save_submission` statement has the expected
    `event_type` and `page` fields.
    """
    statement = mock_instance(ORASaveSubmission)

    assert statement.event_type == "openassessmentblock.save_submission"
    assert statement.page == "x_module"


def test_models_edx_ora_student_training_assess_example_with_valid_statement():
    """Test that a `openassessment.student_training_assess_example` statement
    has the expected `event_type` and `page` fields.
    """
    statement = mock_instance(ORAStudentTrainingAssessExample)

    assert statement.event_type == "openassessment.student_training_assess_example"
    assert statement.page == "x_module"


def test_models_edx_ora_upload_file_example_with_valid_statement():
    """Test that a `openassessment.upload_file` statement
    has the expected `event_type` and `page` fields.
    """
    statement = mock_instance(ORAUploadFile)

    assert statement.event_type == "openassessment.upload_file"
    assert statement.name == "openassessment.upload_file"
