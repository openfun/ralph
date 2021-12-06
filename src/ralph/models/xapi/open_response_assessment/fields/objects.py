"""Open Response Assessment xAPI object field definitions"""

from typing import Optional

from ralph.models.xapi.constants import ACTIVITY_QUESTION_ID

from ...fields.objects import (
    ObjectDefinitionExtensionsField,
    ObjectDefinitionField,
    ObjectField,
)


class QuestionObjectDefinitionField(ObjectDefinitionField):
    """Represents the `object.definition` xAPI field for question saved xAPI statement.

    Attributes:
       type (str): Consists of the value `http://adlnet.gov/expapi/activities/question`.
       extensions (dict): See ObjectDefinitionExtensionsField.
    """

    type: ACTIVITY_QUESTION_ID = ACTIVITY_QUESTION_ID.__args__[0]
    extensions: Optional[ObjectDefinitionExtensionsField]


class QuestionObjectField(ObjectField):
    """Represents the `object` xAPI field for question saved xAPI statement.

    Attributes:
        definition (dict): See PageObjectDefinitionField.
    """

    definition: QuestionObjectDefinitionField = QuestionObjectDefinitionField()
