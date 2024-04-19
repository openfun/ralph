"""Tests for the enrollment event models."""

import json

import pytest

from ralph.models.edx.enrollment.statements import (
    EdxCourseEnrollmentActivated,
    EdxCourseEnrollmentDeactivated,
    EdxCourseEnrollmentModeChanged,
    EdxCourseEnrollmentUpgradeSucceeded,
    UIEdxCourseEnrollmentUpgradeClicked,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
        EdxCourseEnrollmentActivated,
        EdxCourseEnrollmentDeactivated,
        EdxCourseEnrollmentModeChanged,
        EdxCourseEnrollmentUpgradeSucceeded,
        UIEdxCourseEnrollmentUpgradeClicked,
    ],
)
def test_models_edx_edx_course_enrollment_selectors_with_valid_statements(class_):
    """Test given a valid course enrollment edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_course_enrollment_activated_with_valid_statement():
    """Test that a `edx.course.enrollment.activated` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCourseEnrollmentActivated)
    assert statement.event_type == "edx.course.enrollment.activated"
    assert statement.name == "edx.course.enrollment.activated"


def test_models_edx_edx_course_enrollment_deactivated_with_valid_statement():
    """Test that a `edx.course.enrollment.deactivated` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCourseEnrollmentDeactivated)
    assert statement.event_type == "edx.course.enrollment.deactivated"
    assert statement.name == "edx.course.enrollment.deactivated"


def test_models_edx_edx_course_enrollment_mode_changed_with_valid_statement():
    """Test that a `edx.course.enrollment.mode_changed` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCourseEnrollmentModeChanged)
    assert statement.event_type == "edx.course.enrollment.mode_changed"
    assert statement.name == "edx.course.enrollment.mode_changed"


def test_models_edx_ui_edx_course_enrollment_upgrade_clicked_with_valid_statement():
    """Test that a `edx.course.enrollment.upgrade_clicked` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(UIEdxCourseEnrollmentUpgradeClicked)
    assert statement.event_type == "edx.course.enrollment.upgrade_clicked"
    assert statement.name == "edx.course.enrollment.upgrade_clicked"


def test_models_edx_edx_course_enrollment_upgrade_succeeded_with_valid_statement():
    """Test that a `edx.course.enrollment.upgrade.succeeded` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCourseEnrollmentUpgradeSucceeded)
    assert statement.event_type == "edx.course.enrollment.upgrade.succeeded"
    assert statement.name == "edx.course.enrollment.upgrade.succeeded"
