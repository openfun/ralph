"""
Tests for the StudentTrainingAssessExample event schema
"""
from ralph.schemas.edx.ora.student_training_assess_example import (
    StudentTrainingAssessExampleSchema,
)

from tests.schema.edx.test_common import check_loading_valid_events


def test_loading_valid_events_should_not_raise_exceptions():
    """check that loading valid events does not raise exceptions"""
    check_loading_valid_events(
        StudentTrainingAssessExampleSchema(), "student_training_assess_example"
    )
