"""`Audio` activity types definitions."""

import sys

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


# Audio


class AudioActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for audio `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/audio/activity-type/audio`.
    """

    type: Literal["https://w3id.org/xapi/audio/activity-type/audio"] = (
        "https://w3id.org/xapi/audio/activity-type/audio"
    )


class AudioActivity(BaseXapiActivity):
    """Pydantic model for audio `Activity` type.

    Attributes:
        name (dict): Consists of the dictionary `{"en-US": <name of the audio>}`.
        definition (dict): See audioActivityDefinition.
    """

    definition: AudioActivityDefinition
