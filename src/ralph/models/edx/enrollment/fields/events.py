"""Enrollment models event field definition"""

from typing import Literal, Union

from ...base import AbstractBaseEventField


class EnrollmentEventField(AbstractBaseEventField):
    """Represents the `event` field for enrollment events.

    Note: Only server enrollment events require an `event` field.

    Attributes:
        course_id (str): Consists in the course in which the student was enrolled or unenrolled.
        mode (str): Takes either `audit`, `honor`, `professional` or `verified` value.
            It identifies the student’s enrollment mode.
        user_id (int): Identifies the student who was enrolled or unenrolled.
    """

    course_id: str
    mode: Union[
        Literal["audit"], Literal["honor"], Literal["professional"], Literal["verified"]
    ]
    user_id: Union[int, Literal[""], None]
