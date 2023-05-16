"""`AcrossX Profile` activity types definitions."""

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition


# Message
class MessageActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for message `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/acrossx/activities/message`.
    """

    type: Literal[
        "https://w3id.org/xapi/acrossx/activities/message"
    ] = "https://w3id.org/xapi/acrossx/activities/message"


class MessageActivity(BaseXapiActivity):
    """Pydantic model for message `Activity` type.

    Attributes:
        definition (dict): see MessageActivityDefinition.
    """

    definition: MessageActivityDefinition = MessageActivityDefinition()
