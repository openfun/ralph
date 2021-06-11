"""Open Response Assessment xAPI object field definitions"""

from typing import Literal, Optional

from ...base import BaseModelWithConfig
from ...constants import (
    ACTIVITY_QUESTION_DISPLAY,
    ACTIVITY_QUESTION_ID,
    LANG_EN_US_DISPLAY,
)
from ...fields.objects import ObjectDefinitionExtensionsField, ObjectField


class QuestionObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field for question saved xAPI statement.

    WARNING: It doesn't include the recommended `description` field nor the optional `moreInfo`,
    `Interaction properties` and `extensions` fields.

    Attributes:
       name (dict): Consists of the dictionary `{"en-US": "question"}`.
       type (str): Consists of the value `http://adlnet.gov/expapi/activities/question`.
       extensions (dict): See ObjectDefinitionExtensionsField.
    """

    name: dict[Literal[LANG_EN_US_DISPLAY], Literal[ACTIVITY_QUESTION_DISPLAY]] = {
        LANG_EN_US_DISPLAY: ACTIVITY_QUESTION_DISPLAY
    }
    type: Literal[ACTIVITY_QUESTION_ID] = ACTIVITY_QUESTION_ID
    extensions: Optional[ObjectDefinitionExtensionsField]


class QuestionObjectField(ObjectField):
    """Represents the `object` xAPI field for question saved xAPI statement.

    WARNING: It doesn't include the optional `objectType` field.

    Attributes:
        definition (QuestionObjectDefinitionField): See PageObjectDefinitionField.
    """

    definition: QuestionObjectDefinitionField = QuestionObjectDefinitionField()
