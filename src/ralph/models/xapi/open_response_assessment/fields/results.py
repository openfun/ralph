"""Open Response Assessment xAPI events result fields definitions"""

from pydantic import Field

from ralph.models.xapi.config import BaseModelWithConfig
from ralph.models.xapi.constants import EXTENSION_RESPONSES_ID


class QuestionSavedResultExtensionsField(BaseModelWithConfig):
    """Represents the `result.extensions` xAPI field for question saved xAPI statement.

    Attributes:
        responses (list of str): A list of saved responses for the question.
    """

    responses: list[str] = Field(alias=EXTENSION_RESPONSES_ID)


class QuestionSavedResultField(BaseModelWithConfig):
    """Represents the `result` xAPI field for question saved xAPI statement.

    Attributes:
        extensions (dict): see QuestionSavedResultExtensionsField.
    """

    extensions: QuestionSavedResultExtensionsField
