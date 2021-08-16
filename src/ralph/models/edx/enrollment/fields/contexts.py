"""Enrollment event models context fields definitions"""

from typing import Literal, Union

from ...base import BaseContextField


class EdxCourseEnrollmentUpgradeClickedContextField(BaseContextField):
    """Represents the `context` field of the `edx.course.enrollment.upgrade_clicked` server
    statement.

    In addition to the common context member fields, this statement also comprises the `mode`
    context member field.

    Attributes:
        mode (str): Consists of either the `audit` or `honor` value. It identifies the enrollment
        mode when the user clicked <kbd>Challenge Yourself</kbd>.
    """

    mode: Union[Literal["audit"], Literal["honor"]]


class EdxCourseEnrollmentUpgradeSucceededContextField(BaseContextField):
    """Represents the `context` field of the `edx.course.enrollment.upgrade.succeeded` server
    statement.

    In addition to the common context member fields, this statement also comprises the `mode`
    context member field.

    Attributes:
        mode (str): Consists of the `verified` value.
    """

    mode: Literal["verified"]
