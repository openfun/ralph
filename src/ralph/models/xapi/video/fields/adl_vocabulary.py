"""`ADL Vocabulary` activity types definitions."""

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition
from ..constants.adl_vocabulary import ACTIVITY_ID_QUESTION


# Question
class QuestionActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for question `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://adlnet.gov/expapi/activities/question`.
    """

    type: ACTIVITY_ID_QUESTION = ACTIVITY_ID_QUESTION.__args__[0]


class QuestionActivity(BaseXapiActivity):
    """Pydantic model for question `Activity` type.

    Attributes:
        definition (dict): see QuestionActivityDefinition.
    """

    definition: QuestionActivityDefinition = QuestionActivityDefinition()
