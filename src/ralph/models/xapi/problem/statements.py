"""Problem interaction xAPI statement definitions"""

from ralph.models.xapi.base import BaseXapiModel
from ralph.models.xapi.fields.verbs import InteractedVerbField
from ralph.models.xapi.problem.fields.objects import InteractionObjectField
from ralph.models.xapi.problem.fields.results import InteractionInteractedResultField


class InteractionInteracted(BaseXapiModel):
    """Represents an interaction interacted xAPI statement.

    Example: John interacted with the question interaction.

    Attributes:
        object (InteractionObjectField): See InteractionObjectField.
        result (InteractionInteractedResultField): See InteractionInteractedResultField
        verb (InteractedVerbField): See InteractedVerbField.
    """

    object: InteractionObjectField
    result: InteractionInteractedResultField
    verb: InteractedVerbField = InteractedVerbField()
