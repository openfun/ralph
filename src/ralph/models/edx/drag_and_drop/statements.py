"""Drag and drop event model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.edx.drag_and_drop.fields.events import (
    EdxDragAndDropV2FeedbackEventField,
    EdxDragAndDropV2ItemDroppedEventField,
    EdxDragAndDropV2ItemPickedUpEventField,
)
from ralph.models.selector import selector

from ..server import BaseServerModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class EdxDragAndDropV2FeedbackClosed(BaseServerModel):
    """Pydantic model for `edx.drag_and_drop_v2.feedback.closed` statement.

    The server emits this statement when a pop up feedback message closes in a
    drag and drop problem.

    Attributes:
        event (EdxDragAndDropV2FeedbackEventField): See
            EdxDragAndDropV2FeedbackEventField.
        event_type (str): Consists of the value `edx.drag_and_drop_v2.feedback.closed`.
        name (str): Consists either of the value `edx.drag_and_drop_v2.feedback.closed`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.drag_and_drop_v2.feedback.closed"
    )

    event: Union[
        Json[EdxDragAndDropV2FeedbackEventField],
        EdxDragAndDropV2FeedbackEventField,
    ]
    event_type: Literal["edx.drag_and_drop_v2.feedback.closed"]
    name: Literal["edx.drag_and_drop_v2.feedback.closed"]


class EdxDragAndDropV2FeedbackOpened(BaseServerModel):
    """Pydantic model for `edx.drag_and_drop_v2.feedback.opened` statement.

    The server emits this statement when a pop up feedback message opens in a
    drag and drop problem.

    Attributes:
        event (EdxDragAndDropV2FeedbackEventField): See
            EdxDragAndDropV2FeedbackEventField.
        event_type (str): Consists of the value `edx.drag_and_drop_v2.feedback.opened`.
        name (str): Consists either of the value `edx.drag_and_drop_v2.feedback.opened`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.drag_and_drop_v2.feedback.opened"
    )

    event: Union[
        Json[EdxDragAndDropV2FeedbackEventField],
        EdxDragAndDropV2FeedbackEventField,
    ]
    event_type: Literal["edx.drag_and_drop_v2.feedback.opened"]
    name: Literal["edx.drag_and_drop_v2.feedback.opened"]


class EdxDragAndDropV2ItemDropped(BaseServerModel):
    """Pydantic model for `edx.drag_and_drop_v2.item.dropped` statement.

    The server emits this statement when a learner releases a draggable item into a
    target zone in a drag and drop problem.

    Attributes:
        event (EdxDragAndDropV2ItemDroppedEventField): See
            EdxDragAndDropV2ItemDroppedEventField.
        event_type (str): Consists of the value `edx.drag_and_drop_v2.item.dropped`.
        name (str): Consists either of the value `edx.drag_and_drop_v2.item.dropped`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.drag_and_drop_v2.item.dropped"
    )

    event: Union[
        Json[EdxDragAndDropV2ItemDroppedEventField],
        EdxDragAndDropV2ItemDroppedEventField,
    ]
    event_type: Literal["edx.drag_and_drop_v2.item.dropped"]
    name: Literal["edx.drag_and_drop_v2.item.dropped"]


class EdxDragAndDropV2ItemPickedUp(BaseServerModel):
    """Pydantic model for `edx.drag_and_drop_v2.item.picked_up` statement.

    The server emits this statement when a learner selects a draggable item in a
    drag and drop problem.

    Attributes:
        event (EdxDragAndDropV2ItemPickedUpEventField): See
            EdxDragAndDropV2ItemPickedUpEventField.
        event_type (str): Consists of the value `edx.drag_and_drop_v2.item.picked_up`.
        name (str): Consists either of the value `edx.drag_and_drop_v2.item.picked_up`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.drag_and_drop_v2.item.picked_up"
    )

    event: Union[
        Json[EdxDragAndDropV2ItemPickedUpEventField],
        EdxDragAndDropV2ItemPickedUpEventField,
    ]
    event_type: Literal["edx.drag_and_drop_v2.item.picked_up"]
    name: Literal["edx.drag_and_drop_v2.item.picked_up"]


class EdxDragAndDropV2Loaded(BaseServerModel):
    """Pydantic model for `edx.drag_and_drop_v2.loaded` statement.

    The server emits this statement after a drag and drop problem is shown in the LMS.

    Attributes:
        event_type (str): Consists of the value `edx.drag_and_drop_v2.loaded`.
        name (str): Consists either of the value `edx.drag_and_drop_v2.loaded`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.drag_and_drop_v2.loaded"
    )

    event_type: Literal["edx.drag_and_drop_v2.loaded"]
    name: Literal["edx.drag_and_drop_v2.loaded"]
