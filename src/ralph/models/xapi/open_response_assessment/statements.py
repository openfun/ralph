"""Open Response Assessment xAPI statement definitions"""

from ..base import BaseXapiModel
from ..fields.verbs import SavedVerbField
from .fields.objects import QuestionObjectField
from .fields.results import QuestionSavedResultField


class QuestionSaved(BaseXapiModel):
    """Represents a question saved xAPI statement.

    Example: John saved his answer to the Open Response Assessment question.

    Attributes:
       object (PageObjectField): See PageObjectField.
       result (QuestionSavedResultField): See QuestionSavedResultField
       verb (SavedVerbField): See SavedVerbField.
    """

    object: QuestionObjectField
    result: QuestionSavedResultField
    verb: SavedVerbField = SavedVerbField()
