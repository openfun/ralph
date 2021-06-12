"""Problem interaction xAPI events result fields definitions"""

from ralph.models.xapi.config import BaseModelWithConfig


class InteractionInteractedResultField(BaseModelWithConfig):
    """Represents the `result` xAPI field for the interaction interacted xAPI statement.

    Attributes:
        response (str): Consists of the text of the hint that was displayed to the user.
    """

    response: str
