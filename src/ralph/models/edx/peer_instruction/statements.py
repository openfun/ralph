"""Peer instruction events model definitions."""

from typing import Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from pydantic import Json

from ralph.models.selector import selector

from ..server import BaseServerModel
from .fields.events import PeerInstructionEventField


class PeerInstructionAccessed(BaseServerModel):
    """Pydantic model for `ubc.peer_instruction.accessed` statement.

    The server emits this event when a peer instruction question and its set of answer
    choices is shown to a learner.

    Attributes:
        event_type (str): Consists of the value `ubc.peer_instruction.accessed`.
        name (str): Consists of the value `ubc.peer_instruction.accessed`.
    """

    __selector__ = selector(
        event_source="server", event_type="ubc.peer_instruction.accessed"
    )

    event_type: Literal["ubc.peer_instruction.accessed"]
    name: Literal["ubc.peer_instruction.accessed"]


class PeerInstructionOriginalSubmitted(BaseServerModel):
    """Pydantic model for `ubc.peer_instruction.original_submitted` statement.

    The server emits this event when learners submit their initial responses. These
    events record the answer choice the learner selected and the explanation given
    for why that selection was made.

    Attributes:
        event (int): See PeerInstructionEventField.
        event_type (str): Consists of the value
            `ubc.peer_instruction.original_submitted`.
        name (str): Consists of the value `ubc.peer_instruction.original_submitted`.
    """

    __selector__ = selector(
        event_source="server", event_type="ubc.peer_instruction.original_submitted"
    )

    event: Union[
        Json[PeerInstructionEventField],  # pylint: disable=unsubscriptable-object
        PeerInstructionEventField,
    ]
    event_type: Literal["ubc.peer_instruction.original_submitted"]
    name: Literal["ubc.peer_instruction.original_submitted"]


class PeerInstructionRevisedSubmitted(BaseServerModel):
    """Pydantic model for `ubc.peer_instruction.revised_submitted` statement.

    The server emits this event when learners submit their revised responses. These
    events record the answer choice selected by the learner and the explanation for
    why that selection was made.

    Attributes:
        event (int): See PeerInstructionEventField.
        event_type (str): Consists of the value
            `ubc.peer_instruction.revised_submitted`.
        name (str): Consists of the value `ubc.peer_instruction.revised_submitted`.
    """

    __selector__ = selector(
        event_source="server", event_type="ubc.peer_instruction.revised_submitted"
    )

    event: Union[
        Json[PeerInstructionEventField],  # pylint: disable=unsubscriptable-object
        PeerInstructionEventField,
    ]
    event_type: Literal["ubc.peer_instruction.revised_submitted"]
    name: Literal["ubc.peer_instruction.revised_submitted"]
