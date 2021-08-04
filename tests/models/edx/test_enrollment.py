"""Tests for the enrollment event models"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.edx.enrollment.fields.contexts import (
    EdxCourseEnrollmentUpgradeClickedContextField,
    EdxCourseEnrollmentUpgradeSucceededContextField,
)
from ralph.models.edx.enrollment.fields.events import EnrollmentEventField
from ralph.models.edx.enrollment.statements import (
    EdxCourseEnrollmentActivated,
    EdxCourseEnrollmentDeactivated,
    EdxCourseEnrollmentModeChanged,
    EdxCourseEnrollmentUpgradeSucceeded,
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
def test_models_edx_edx_course_enrollment_activated_with_valid_statement(
    statement,
):
    """Tests that a `edx.course.enrollment.activated` statement has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "edx.course.enrollment.activated"
    assert statement.name == "edx.course.enrollment.activated"


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentActivated,
        referer=provisional.urls(),
        event=st.builds(EnrollmentEventField),
    )
)
def test_models_edx_edx_course_enrollment_activated_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.course.enrollment.activated` statement the `get_model` selector method
    should return `EdxCourseEnrollmentActivated` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_edx_course_enrollment_deactivated_with_valid_statement(
    statement,
):
    """Tests that a `edx.course.enrollment.deactivated` statement has the expected `event_type` and
    `name`.
    """

    assert statement.event_type == "edx.course.enrollment.deactivated"
    assert statement.name == "edx.course.enrollment.deactivated"


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentDeactivated,
        referer=provisional.urls(),
        event=st.builds(EnrollmentEventField),
    )
)
def test_models_edx_edx_course_enrollment_deactivated_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.course.enrollment.deactivated` statement the `get_model` selector method
    should return `EdxCourseEnrollmentDeactivated` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_edx_course_enrollment_mode_changed_with_valid_statement(
    statement,
):
    """Tests that a `edx.course.enrollment.mode_changed` statement has the expected `event_type`
    and `name`.
    """

    assert statement.event_type == "edx.course.enrollment.mode_changed"
    assert statement.name == "edx.course.enrollment.mode_changed"


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentModeChanged,
        referer=provisional.urls(),
        event=st.builds(EnrollmentEventField),
    )
)
def test_models_edx_edx_course_enrollment_mode_changed_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.course.enrollment.mode_changed` statement the `get_model` selector method
    should return `EdxCourseEnrollmentModeChanged` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_ui_edx_course_enrollment_upgrade_clicked_with_valid_statement(
    statement,
):
    """Tests that a `edx.course.enrollment.upgrade_clicked` statement has the expected `event_type`
    and `name`.
    """

    assert statement.event_type == "edx.course.enrollment.upgrade_clicked"
    assert statement.name == "edx.course.enrollment.upgrade_clicked"


@settings(max_examples=1)
@given(
    st.builds(
        UIEdxCourseEnrollmentUpgradeClicked,
        referer=provisional.urls(),
        page=provisional.urls(),
        context=st.builds(EdxCourseEnrollmentUpgradeClickedContextField),
    )
)
def test_models_edx_ui_edx_course_enrollment_upgrade_clicked_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.course.enrollment.upgrade_clicked` statement the `get_model` selector
    method should return `UIEdxCourseEnrollmentUpgradeClicked` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
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
def test_models_edx_edx_course_enrollment_upgrade_succeeded_with_valid_statement(
    statement,
):
    """Tests that a `edx.course.enrollment.upgrade.succeeded` statement has the expected
    `event_type` and `name`.
    """

    assert statement.event_type == "edx.course.enrollment.upgrade.succeeded"
    assert statement.name == "edx.course.enrollment.upgrade.succeeded"


@settings(max_examples=1)
@given(
    st.builds(
        EdxCourseEnrollmentUpgradeSucceeded,
        referer=provisional.urls(),
        context=st.builds(EdxCourseEnrollmentUpgradeSucceededContextField),
    )
)
def test_models_edx_edx_course_enrollment_upgrade_succeeded_selector_with_valid_statement(
    statement,
):
    """Tests given a `edx.course.enrollment.upgrade.succeeded` statement the `get_model` selector
    method should return `EdxCourseEnrollmentUpgradeSucceeded` model.
    """

    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(statement)
        is EdxCourseEnrollmentUpgradeSucceeded
    )
