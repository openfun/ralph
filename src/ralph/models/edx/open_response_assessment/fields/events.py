"""Open Response Assessment events model event fields definitions"""

from typing import Literal, Union

from pydantic import Json

from ralph.models.edx.base import AbstractBaseEventField, BaseModelWithConfig


class ORASaveSubmissionEventSavedResponseField(BaseModelWithConfig):
    """Represents the `openassessmentblock.save_submission` event saved_response field.

    Attributes:
        parts (list): Consists of a list of dictionaries `{"text": <response value>}`.
    """

    parts: list[dict[Literal["text"], str]]


class ORASaveSubmissionEventField(AbstractBaseEventField):
    """Represents the `event` field of `openassessmentblock.save_submission` model.

    Attributes:
        saved_response (str): Consist of a JSON string of the users saved responses.
            Note:
                Responses have a length limit of 100000 in the front-end but not in the
                back-end.
                Events are truncated at `TRACK_MAX_EVENT` which is 50000 by default.
                Also the `eventtracking.backends.logger.LoggerBackend` silently drops
                events when they exceed `TRACK_MAX_EVENT`.
    """

    # pylint: disable=unsubscriptable-object
    saved_response: Union[
        Json[ORASaveSubmissionEventSavedResponseField],
        ORASaveSubmissionEventSavedResponseField,
    ]
