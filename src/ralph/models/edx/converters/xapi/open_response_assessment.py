"""Open Response Assessment xAPI Converters"""

from ralph.models.converter import ConversionItem
from ralph.models.edx.open_response_assessment import ORASaveSubmission
from ralph.models.xapi.constants import EXTENSION_RESPONSES_ID
from ralph.models.xapi.open_response_assessment.statements import QuestionSaved

from .base import BaseXapiConverter


class ORASaveSubmissionToQuestionSaved(BaseXapiConverter):
    """Converts an edX `openassessmentblock.save_submission` event to xAPI.

    Example: John saved his answer to the Open Response Assessment question.
    """

    __src__ = ORASaveSubmission
    __dest__ = QuestionSaved

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "object__id",
                    "context__module__usage_key",
                    lambda usage_key: f"{self.home_page}/{usage_key}",
                ),
                ConversionItem(
                    "result__extensions__" + EXTENSION_RESPONSES_ID,
                    "event__saved_response__parts",
                    lambda parts: [part["text"] for part in parts],
                ),
            }
        )
