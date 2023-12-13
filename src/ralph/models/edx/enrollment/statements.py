"""Enrollment event model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from ..server import BaseServerModel
from .fields.contexts import (
    EdxCourseEnrollmentUpgradeClickedContextField,
    EdxCourseEnrollmentUpgradeSucceededContextField,
)
from .fields.events import EnrollmentEventField

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class EdxCourseEnrollmentActivated(BaseServerModel):
    """Pydantic model for `edx.course.enrollment.activated` statement.

    The server emits this statement when a student enrolls in a course.

    Attributes:
        event (EnrollmentEventField): See EnrollmentEventField.
        event_type (str): Consists of the value `edx.course.enrollment.activated`.
        name (str): Consists of the value `edx.course.enrollment.activated`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.activated"
    )
    event: Union[
        Json[EnrollmentEventField],
        EnrollmentEventField,
    ]
    event_type: Literal["edx.course.enrollment.activated"]
    name: Literal["edx.course.enrollment.activated"]


class EdxCourseEnrollmentDeactivated(BaseServerModel):
    """Pydantic model for `edx.course.enrollment.deactivated` statement.

    The server emits this statement when a student unenrolls from a course.

    Attributes:
        event (EnrollmentEventField): See EnrollmentEventField.
        event_type (str): Consists of the value `edx.course.enrollment.deactivated`.
        name (str): Consists of the value `edx.course.enrollment.deactivated`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.deactivated"
    )


    event: Json[EnrollmentEventField]
    # event: Union[
    #     Json[EnrollmentEventField],
    #     EnrollmentEventField,
    # ]
    event_type: Literal["edx.course.enrollment.deactivated"]
    name: Literal["edx.course.enrollment.deactivated"]


class EdxCourseEnrollmentModeChanged(BaseServerModel):
    """Pydantic model for `edx.course.enrollment.mode_changed` statement.

    The server emits this statement when the process of changing a student’s
    student_courseenrollment.mode to a different mode is complete.

    Attributes:
        event (EnrollmentEventField): See EnrollmentEventField.
        event_type (str): Consists of the value `edx.course.enrollment.mode_changed`.
        name (str): Consists of the value `edx.course.enrollment.mode_changed`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.course.enrollment.mode_changed"
    )


    event: Json[EnrollmentEventField]
    # event: Union[
    #     EnrollmentEventField,
    #     Json[EnrollmentEventField],
    # ]
    event_type: Literal["edx.course.enrollment.mode_changed"]
    name: Literal["edx.course.enrollment.mode_changed"]


class UIEdxCourseEnrollmentUpgradeClicked(BaseBrowserModel):
    """Pydantic model for `edx.course.enrollment.upgrade_clicked` statement.

    The browser emits this statement when a student clicks <kbd>ChallengeYourself</kbd>
    option, and the process of upgrading the student_courseenrollment.mode for the
    student to `verified` begins.

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
    """Pydantic model for `edx.course.enrollment.upgrade.succeeded` statement.

    The server emits this statement when the process of upgrading a student’s
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
