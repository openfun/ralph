"""Enrollment event model definitions"""

from typing import Literal, Union

from pydantic import Json

from ralph.models.selector import selector

from ..browser import BaseBrowserEvent
from ..server import BaseServerEvent
from .fields.contexts import (
    EdxCourseEnrollmentUpgradeClickedContextField,
    EdxCourseEnrollmentUpgradeSucceededContextField,
)
from .fields.events import EnrollmentEventField


class EdxCourseEnrollmentActivated(BaseServerEvent):
    """Represents the `edx.course.enrollment.activated` server event.

    When a student enrolls in a course, the server emits this event.

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


class EdxCourseEnrollmentDeactivated(BaseServerEvent):
    """Represents the `edx.course.enrollment.deactivated` server event.

    When a student unenrolls from a course, the server emits this event.

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


class EdxCourseEnrollmentModeChanged(BaseServerEvent):
    """Represents the `edx.course.enrollment.mode_changed` server event.

    The server emits this event when the process of changing a student’s
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


class UIEdxCourseEnrollmentUpgradeClicked(BaseBrowserEvent):
    """Represents the `edx.course.enrollment.upgrade_clicked` browser event.

    The browser emits this event when a student clicks <kbd>ChallengeYourself</kbd> option,
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


class EdxCourseEnrollmentUpgradeSucceeded(BaseServerEvent):
    """Represents the `edx.course.enrollment.upgrade.succeeded` server event.

    The server emits this event when the process of upgrading a student’s
    student_courseenrollment.mode from `audit` or `honor` to `verified` is complete.

    Attributes:
        context (EdxCourseEnrollmentUpgradeSucceededContextField):
            See EdxCourseEnrollmentUpgradeSucceededContextField.
        event_type (str): Consists of the value `edx.course.enrollment.upgrade.succeeded`.
        name (str): Consists of the value `edx.course.enrollment.upgrade.succeeded`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.upgrade.succeeded"
    )

    context: EdxCourseEnrollmentUpgradeSucceededContextField
    event_type: Literal["edx.course.enrollment.upgrade.succeeded"]
    name: Literal["edx.course.enrollment.upgrade.succeeded"]
