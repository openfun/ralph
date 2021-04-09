"""Tests for the enrollment event models"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.edx.enrollment import (
    EdxCourseEnrollmentActivated,
    EdxCourseEnrollmentDeactivated,
    EdxCourseEnrollmentModeChanged,
    EdxCourseEnrollmentUpgradeClickedContextField,
    EdxCourseEnrollmentUpgradeSucceeded,
    EdxCourseEnrollmentUpgradeSucceededContextField,
    EnrollmentEventField,
    UIEdxCourseEnrollmentUpgradeClicked,
)
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentActivated,
        referer=provisional.urls(),
        event=st.builds(EnrollmentEventField),
    )
)
def test_models_edx_edx_course_enrollment_activated_selector_with_valid_event(event):
    """Tests given an edx.course.enrollment.activated event
    the get_model method should return EdxCourseEnrollmentActivated model.
    """

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is EdxCourseEnrollmentActivated
    )


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentDeactivated,
        referer=provisional.urls(),
        event=st.builds(EnrollmentEventField),
    )
)
def test_models_edx_edx_course_enrollment_deactivated_selector_with_valid_event(event):
    """Tests given an edx.course.enrollment.deactivated event
    the get_model method should return EdxCourseEnrollmentDeactivated model.
    """

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is EdxCourseEnrollmentDeactivated
    )


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentModeChanged,
        referer=provisional.urls(),
        event=st.builds(EnrollmentEventField),
    )
)
def test_models_edx_edx_course_enrollment_mode_changed_selector_with_valid_event(event):
    """Tests given an edx.course.enrollment.mode_changed event
    the get_model method should return EdxCourseEnrollmentModeChanged model.
    """

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is EdxCourseEnrollmentModeChanged
    )


@settings(max_examples=1)
@given(
    st.builds(
        UIEdxCourseEnrollmentUpgradeClicked,
        referer=provisional.urls(),
        page=provisional.urls(),
        context=st.builds(EdxCourseEnrollmentUpgradeClickedContextField),
    )
)
def test_models_edx_ui_edx_course_enrollment_upgrade_clicked_selector_with_valid_event(
    event,
):
    """Tests given an edx.course.enrollment.upgrade_clicked event
    the get_model method should return UIEdxCourseEnrollmentUpgradeClicked model.
    """

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is UIEdxCourseEnrollmentUpgradeClicked
    )


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentUpgradeSucceeded,
        referer=provisional.urls(),
        context=st.builds(EdxCourseEnrollmentUpgradeSucceededContextField),
    )
)
def test_models_edx_edx_course_enrollment_upgrade_succeeded_selector_with_valid_event(
    event,
):
    """Tests given an edx.course.enrollment.upgrade.succeeded event
    the get_model method should return EdxCourseEnrollmentUpgradeSucceeded model.
    """

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event)
        is EdxCourseEnrollmentUpgradeSucceeded
    )
