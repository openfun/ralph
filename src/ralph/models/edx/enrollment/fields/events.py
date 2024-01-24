"""Enrollment models event field definition."""

import sys
from typing import Union

from ...base import AbstractBaseEventField

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class EnrollmentEventField(AbstractBaseEventField):
    """Pydantic model for enrollment `event` field.

    Note: Only server enrollment statements require an `event` field.

    Attributes:
        course_id (str): Consists in the course in which the student was enrolled or
            unenrolled.
        mode (str): Takes either `audit`, `honor`, `professional` or `verified` value.
            It identifies the student’s enrollment mode.
        user_id (int): Identifies the student who was enrolled or unenrolled.
    """

    course_id: str
    mode: Union[
        Literal["audit"], Literal["honor"], Literal["professional"], Literal["verified"]
    ]
    user_id: Union[int, Literal[""], None] = None
