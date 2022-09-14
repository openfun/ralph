"""Navigational event field definition."""

from pydantic import constr

from ...base import AbstractBaseEventField


class NavigationalEventField(AbstractBaseEventField):
    """Represents the `event` field of navigational statements.

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

    id: constr(
        regex=(
            r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type"  # noqa : F722
            r"@sequential\+block@[a-f0-9]{32}$"  # noqa : F722
        )
    )
    new: int
    old: int
