"""Problem interaction event model definitions"""

from typing import Literal

from pydantic import constr

from ralph.models.edx.base import AbstractBaseEventField
from ralph.models.edx.x_block import BaseXBlockEvent
from ralph.models.selector import selector


class DemandhintDisplayedEventField(AbstractBaseEventField):
    """Represents the `edx.problem.hint.demandhint_displayed` event field.

    Attributes:
        hint_index (int): Consists of the identifier for the hint that was displayed to the user.
            Note:
                The first hint defined for a problem is identified with hint_index: 0.
        hint_len (int): Consists of the total number of hints defined for this problem.
        hint_text (str): Consists of the text of the hint that was displayed to the user.
        module_id (str): Consists of the identifier for the problem component for which the user
            requested the hint.
            Note:
                The `module_id` is equal to the `context.module.usage_key` of the event.
    """

    hint_index: int
    hint_len: int
    hint_text: str
    module_id: str


class DemandhintDisplayed(BaseXBlockEvent):
    """Represents the `edx.problem.hint.demandhint_displayed` event.

    This event is triggered when the user requests a hint for a problem.

    Attributes:
        event_type (str): Consists of the value `edx.problem.hint.demandhint_displayed`.
        event (dict): See DemandhintDisplayedEventField.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.problem.hint.demandhint_displayed"
    )

    event_type: Literal["edx.problem.hint.demandhint_displayed"]
    event: DemandhintDisplayedEventField


class Showanswer(BaseXBlockEvent):
    """Represents the `showanswer` event.

    This event is triggered when the user requests the answer for a problem.

    Attributes:
        event_type (str): Consists of the value `showanswer`.
        event (dict): Consists of a dictionary holding the block ID of the current problem.
            Note:
                The `problem_id` is equal to the `context.module.usage_key` of the event.
    """

    __selector__ = selector(event_source="server", event_type="showanswer")

    event_type: Literal["showanswer"]
    event: dict[
        Literal["problem_id"],
        constr(regex=r"^block-v1:.+\+.+\+.+type@.+@[a-f0-9]{32}$"),  # noqa:F722
    ]
