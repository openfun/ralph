"""Open Response Assessment xAPI statement definitions"""

from ...selector import selector
from ..base import BaseXapiModel
from ..constants import ACTIVITY_QUESTION_ID, VERB_SAVED_ID
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

    __selector__ = selector(
        object__definition__type=ACTIVITY_QUESTION_ID.__args__[0],
        verb__id=VERB_SAVED_ID.__args__[0],
    )

    object: QuestionObjectField
    result: QuestionSavedResultField
    verb: SavedVerbField = SavedVerbField()
