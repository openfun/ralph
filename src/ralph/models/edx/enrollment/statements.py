"""Enrollment event model definitions"""

from typing import Literal, Union

from pydantic import Json

from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from ..server import BaseServerModel
from .fields.contexts import (
    EdxCourseEnrollmentUpgradeClickedContextField,
    EdxCourseEnrollmentUpgradeSucceededContextField,
)
from .fields.events import EnrollmentEventField


class EdxCourseEnrollmentActivated(BaseServerModel):
    """Represents the `edx.course.enrollment.activated` server statement.

    The server emits it when a student enrolls in a course.

    Attributes:
        event (EnrollmentEventField): See EnrollmentEventField.
        event_type (str): Consists of the value `edx.course.enrollment.activated`.
        name (str): Consists of the value `edx.course.enrollment.activated`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.activated"
    )

    event: Union[
        Json[EnrollmentEventField],  # pylint: disable=unsubscriptable-object
        EnrollmentEventField,
    ]
    event_type: Literal["edx.course.enrollment.activated"]
    name: Literal["edx.course.enrollment.activated"]


class EdxCourseEnrollmentDeactivated(BaseServerModel):
    """Represents the `edx.course.enrollment.deactivated` server statement.

    The server emits it when a student unenrolls from a course.

    Attributes:
        event (EnrollmentEventField): See EnrollmentEventField.
        event_type (str): Consists of the value `edx.course.enrollment.deactivated`.
        name (str): Consists of the value `edx.course.enrollment.deactivated`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.deactivated"
    )

    event: Union[
        Json[EnrollmentEventField],  # pylint: disable=unsubscriptable-object
        EnrollmentEventField,
    ]
    event_type: Literal["edx.course.enrollment.deactivated"]
    name: Literal["edx.course.enrollment.deactivated"]


class EdxCourseEnrollmentModeChanged(BaseServerModel):
    """Represents the `edx.course.enrollment.mode_changed` server statement.

    The server emits it when the process of changing a student’s
    student_courseenrollment.mode to a different mode is complete.

    Attributes:
        event (EnrollmentEventField): See EnrollmentEventField.
        event_type (str): Consists of the value `edx.course.enrollment.mode_changed`.
        name (str): Consists of the value `edx.course.enrollment.mode_changed`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.mode_changed"
    )

    event: Union[
        Json[EnrollmentEventField],  # pylint: disable=unsubscriptable-object
        EnrollmentEventField,
    ]
    event_type: Literal["edx.course.enrollment.mode_changed"]
    name: Literal["edx.course.enrollment.mode_changed"]


class UIEdxCourseEnrollmentUpgradeClicked(BaseBrowserModel):
    """Represents the `edx.course.enrollment.upgrade_clicked` browser statement.

    The browser emits it when a student clicks <kbd>ChallengeYourself</kbd> option,
    and the process of upgrading the student_courseenrollment.mode for the student
    to `verified` begins.

    Attributes:
        context (EdxCourseEnrollmentUpgradeClickedContextField):
            See EdxCourseEnrollmentUpgradeClickedContextField.
        event_type (str): Consists of the value `edx.course.enrollment.upgrade_clicked`.
        name (str): Consists of the value `edx.course.enrollment.upgrade_clicked`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.enrollment.upgrade_clicked"
    )

    context: EdxCourseEnrollmentUpgradeClickedContextField
    event_type: Literal["edx.course.enrollment.upgrade_clicked"]
    name: Literal["edx.course.enrollment.upgrade_clicked"]


class EdxCourseEnrollmentUpgradeSucceeded(BaseServerModel):
    """Represents the `edx.course.enrollment.upgrade.succeeded` server statement.

    The server emits it when the process of upgrading a student’s
    student_courseenrollment.mode from `audit` or `honor` to `verified` is complete.

    Attributes:
        context (EdxCourseEnrollmentUpgradeSucceededContextField):
            See EdxCourseEnrollmentUpgradeSucceededContextField.
        event_type (str): Consists of the value
            `edx.course.enrollment.upgrade.succeeded`.
        name (str): Consists of the value `edx.course.enrollment.upgrade.succeeded`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.upgrade.succeeded"
    )

    context: EdxCourseEnrollmentUpgradeSucceededContextField
    event_type: Literal["edx.course.enrollment.upgrade.succeeded"]
    name: Literal["edx.course.enrollment.upgrade.succeeded"]
