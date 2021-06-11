"""Open Response Assessment event model definitions"""

from typing import Literal, Union

from pydantic.types import Json

from ralph.models.edx.base import AbstractBaseEventField, BaseModelWithConfig
from ralph.models.edx.x_block import BaseXBlockEvent
from ralph.models.selector import selector


class ORASaveSubmissionEventSavedResponseField(BaseModelWithConfig):
    """Represents the `openassessmentblock.save_submission` event saved_response field.

    Attributes:
        parts: Consists of a list of dictionaries with a `text` key holding the response value.
    """

    parts: list[dict[Literal["text"], str]]


class ORASaveSubmissionEventField(AbstractBaseEventField):
    """Represents the `openassessmentblock.save_submission` event field.

    Attributes:
        saved_response (str): Consist of a JSON string holding the users saved responses.
            Note:
                Responses have a length limit of 100000 in the front-end but not in the back-end.
                Events are truncated at `TRACK_MAX_EVENT` length which is 50000 by default.
                Also the `eventtracking.backends.logger.LoggerBackend` silently drops events when
                they exceed `TRACK_MAX_EVENT`.
    """

    # pylint: disable=unsubscriptable-object
    saved_response: Union[
        Json[ORASaveSubmissionEventSavedResponseField],
        ORASaveSubmissionEventSavedResponseField,
    ]


class ORASaveSubmission(BaseXBlockEvent):
    """Represents the `openassessmentblock.save_submission` event.

    This event is triggered when the user clicks on the `Save you progress` button
    to save the current state of his response to an open assessment question.

    Attributes:
        event_type (str): Consists of the value `openassessmentblock.save_submission`.
        event (str): See ORASaveSubmissionEventField.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.save_submission"
    )

    event_type: Literal["openassessmentblock.save_submission"]
    event: ORASaveSubmissionEventField
