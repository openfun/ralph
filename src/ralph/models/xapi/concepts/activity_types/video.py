"""`Video` activity types definitions."""

from typing import Dict, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition
from ...constants import LANG_EN_US_DISPLAY

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

    WARNING: Contains an optional name property, this is not a violation of
    conformity but goes against xAPI specification recommendations.

    Attributes:
        name (dict): Consists of the dictionary `{"en-US": <name of the video>}`.
        definition (dict): See VideoActivityDefinition.
    """

    name: Optional[Dict[Literal[LANG_EN_US_DISPLAY], str]] = None # TODO: validate that this is the behavior we want
    definition: VideoActivityDefinition = VideoActivityDefinition()
