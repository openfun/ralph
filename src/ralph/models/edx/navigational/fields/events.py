"""Navigational event field definition."""

from pydantic import StringConstraints
from typing_extensions import Annotated

from ...base import AbstractBaseEventField


class NavigationalEventField(AbstractBaseEventField):
    """Pydantic model for navigational `event` field.

    Note: All navigational statements are emitted from the browser.

    Attributes:
        id (str): Consists of the edX ID of the sequence.
        old (int): For `seq_goto`, it consists of the index of the unit being jumped to.
            For `seq_next` and `seq_prev`, it consists of the index of the unit being
            navigated to.
        new (int): For `seq_goto`, it consists of the index of the unit being jumped
            from. For `seq_next` and `seq_prev`, it consists of the index of the unit
            being navigated away from.
    """

    id: Annotated[
        str,
        StringConstraints(
            pattern=(
                r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type"  # noqa : F722
                r"@sequential\+block@[a-f0-9]{32}$"  # noqa : F722
            )
        ),
    ]
    new: int
    old: int
