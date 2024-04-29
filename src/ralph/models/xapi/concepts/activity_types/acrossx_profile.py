"""`AcrossX Profile` activity types definitions."""

import sys

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


# Message


class MessageActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for message `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/acrossx/activities/message`.
    """

    type: Literal["https://w3id.org/xapi/acrossx/activities/message"] = (
        "https://w3id.org/xapi/acrossx/activities/message"
    )


class MessageActivity(BaseXapiActivity):
    """Pydantic model for message `Activity` type.

    Attributes:
        definition (dict): see MessageActivityDefinition.
    """

    definition: MessageActivityDefinition = MessageActivityDefinition()


# Webpage


class WebpageActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for webpage `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/acrossx/activities/webpage`.
    """

    type: Literal["https://w3id.org/xapi/acrossx/activities/webpage"] = (
        "https://w3id.org/xapi/acrossx/activities/webpage"
    )


class WebpageActivity(BaseXapiActivity):
    """Pydantic model for webpage `Activity` type.

    Attributes:
        definition (dict): see WebpageActivityDefinition.
    """

    definition: WebpageActivityDefinition
