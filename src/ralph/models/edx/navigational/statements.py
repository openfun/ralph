"""Navigational event model definitions"""

from typing import Literal, Union

from pydantic import Json, validator

from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from .fields.events import NavigationalEventField


class UIPageClose(BaseBrowserModel):
    """Represents the `page_close` browser statement.

    This type of statement is triggered when the user navigates to the next page
    or closes the browser window (when the JavaScript `window.onunload` event
    is called).

    Attributes:
        event (str): Consists of the string value `{}`.
        event_type (str): Consists of the value `page_close`.
        name (str): Consists of the value `page_close`.
    """

    __selector__ = selector(event_source="browser", event_type="page_close")

    # pylint: disable=unsubscriptable-object
    event: Literal["{}"]
    event_type: Literal["page_close"]
    name: Literal["page_close"]


class UISeqGoto(BaseBrowserModel):
    """Represents the `seq_goto` browser statement.

    The browser emits such statement when a user selects a navigational control.
    `seq_goto` is emitted when a user jumps between units in a sequence.

    Attributes:
        event (obj): Consists of member fields that identify specifics triggered event.
        event_type (str): Consists of the value `seq_goto`.
        name (str): Consists of the value `seq_goto`.
    """

    __selector__ = selector(event_source="browser", event_type="seq_goto")

    # pylint: disable=unsubscriptable-object
    event: Union[Json[NavigationalEventField], NavigationalEventField]
    event_type: Literal["seq_goto"]
    name: Literal["seq_goto"]


class UISeqNext(BaseBrowserModel):
    """Represents the `seq_next` browser statement.

    The browser emits such statement when a user selects a navigational control.
    `seq_next` is emitted when a user navigates to the next unit in a sequence.

    Attributes:
        event (obj): Consists of member fields that identify specifics triggered event.
        event_type (str): Consists of the value `seq_next`.
        name (str): Consists of the value `seq_next`.
    """

    __selector__ = selector(event_source="browser", event_type="seq_next")

    # pylint: disable=unsubscriptable-object
    event: Union[Json[NavigationalEventField], NavigationalEventField]
    event_type: Literal["seq_next"]
    name: Literal["seq_next"]

    @validator("event")
    @classmethod
    def validate_next_jump_event_field(cls, value):
        """Checks that event.new is equal to event.old + 1."""

        if value.new != value.old + 1:
            raise ValueError("event.new - event.old should be equal to 1")

        return value


class UISeqPrev(BaseBrowserModel):
    """Represents the `seq_prev` browser statement.

    The browser emits such statement when a user selects a navigational control.
    `seq_prev` is emitted when a user navigates to the previous unit in a sequence.

    Attributes:
        event (obj): Consists of member fields that identify specifics triggered event.
        event_type (str): Consists of the value `seq_prev`.
        name (str): Consists of the value `seq_prev`.

    """

    __selector__ = selector(event_source="browser", event_type="seq_prev")

    # pylint: disable=unsubscriptable-object
    event: Union[Json[NavigationalEventField], NavigationalEventField]
    event_type: Literal["seq_prev"]
    name: Literal["seq_prev"]

    @validator("event")
    @classmethod
    def validate_prev_jump_event_field(cls, value):
        """Checks that event.new is equal to event.old - 1."""

        if value.new != value.old - 1:
            raise ValueError("event.old - event.new should be equal to 1")

        return value
