"""Peer instruction event field definition."""

from pydantic import constr

from ...base import AbstractBaseEventField


class PeerInstructionEventField(AbstractBaseEventField):
    """Pydantic model for peer instruction `event` field.

    Attributes:
        answer (int): Consists of the index assigned to the answer choice selected by
            the learner.
        rationale (str): Consists of the text entered by the learner to explain why
            they selected that answer choice.
        truncated (bool): `True` only if the rationale was longer than 12,500
            characters, which is the maximum included in the event.
    """

    answer: int
    rationale: constr(max_length=12500)
    truncated: bool
