"""Video event fields definitions."""

from typing import Optional

from ...base import AbstractBaseEventField


class EdxDragAndDropV2FeedbackEventField(AbstractBaseEventField):
    """Pydantic model for drag and drop feedback statements `event` field.

    Attributes:
        content (str): Consists of the text of the success or error feedback
            message in the pop up.
        manually (bool): Set to `true` when the learner manually closed the pop up
        dialog box, `false` when the browser closed it.
        truncated (bool): Set to `true` if the content was longer than 12500 characters.
    """

    content: str
    manually: bool
    truncated: Optional[bool]


class EdxDragAndDropV2ItemDroppedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.drag_and_drop_v2.item.dropped` `event` field.

    Attributes:
        input (int): Consists of the number input value entered by the learner.
        item (str): Consists of the display name of the draggable item selected
            by the learner or the item's image URL either.
        item_id (int): Consists of the index assigned to the draggable item
            selected by the learner.
        is_correct (bool): Set to `true` if the item is in the correct zone,
            `false` either. For problems that require a number input, set to `true`
            if the item is dropped in the correct zone and the number input is
            correct, `false` either.
        is_correct_location (bool): Set to `true` if the draggable item is in
            the correct target zone, `false` either. For problems requiring a number
            input, it is equivalent to `is_correct`.
        location (str): Consists of the text identifier for the target zone in
            which the learner placed the item.
        location_id ((int): Consists of the automatically generated unique index
            assigned to the target zone in which the learner placed the item.
    """

    input: int
    item: Optional[str]
    item_id: int
    is_correct: bool
    is_correct_location: bool
    location: str
    location_id: Optional[int]


class EdxDragAndDropV2ItemPickedUpEventField(AbstractBaseEventField):
    """Pydantic model for `edx.drag_and_drop_v2.item.picked_up` `event` field.

    Attributes:
        item_id (int): Consists of the index assigned to the draggable item
            selected by the learner.
    """

    item_id: int
