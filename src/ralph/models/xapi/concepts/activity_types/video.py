"""`Video` activity types definitions."""

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

# Video


class VideoActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for video `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/video/activity-type/video`.
    """

    type: Literal[
        "https://w3id.org/xapi/video/activity-type/video"
    ] = "https://w3id.org/xapi/video/activity-type/video"


class VideoActivity(BaseXapiActivity):
    """Pydantic model for video `Activity` type.

    Attributes:
        definition (dict): See VideoActivityDefinition.
    """

    definition: VideoActivityDefinition = VideoActivityDefinition()
