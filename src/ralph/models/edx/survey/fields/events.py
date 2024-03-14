"""Survey event fields definitions."""

from ...base import AbstractBaseEventField


class XBlockSurveySubmittedEventField(AbstractBaseEventField):
    """Pydantic model for `xblock.survey.submitted` `event` field.

    Attributes:
        url_name (str): Consists of the unique location identifier for the survey.
        choices (dict): Consists of a dict of answers selected for each question
            of the poll (with format `{"question_name":"answer_name"}`)
    """

    url_name: str
    choices: dict
