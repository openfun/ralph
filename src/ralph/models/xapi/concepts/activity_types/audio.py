"""`Audio` activity types definitions."""

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

# Audio


class AudioActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for audio `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/audio/activity-type/audio`.
    """

    type: Literal["https://w3id.org/xapi/audio/activity-type/audio"]


class AudioActivity(BaseXapiActivity):
    """Pydantic model for audio `Activity` type.

    Attributes:
        name (dict): Consists of the dictionary `{"en-US": <name of the audio>}`.
        definition (dict): See audioActivityDefinition.
    """

    definition: AudioActivityDefinition
