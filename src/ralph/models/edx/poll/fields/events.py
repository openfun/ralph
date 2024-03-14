"""Poll event fields definitions."""

from ...base import AbstractBaseEventField


class XBlockPollSubmittedEventField(AbstractBaseEventField):
    """Pydantic model for `xblock.poll.submitted` `event` field.

    Attributes:
        url_name (str): Consists of the unique location identifier for the survey.
        choice (str): Consists of the unique internal identifier for the
            response that the user submitted.
    """

    url_name: str
    choice: str
