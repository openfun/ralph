"""Video xAPI events object fields definitions."""

from typing import Optional

from ...constants import LANG_EN_US_DISPLAY
from ...fields.objects import ObjectDefinitionExtensionsField
from ...fields.unnested_objects import ActivityObjectField, ObjectDefinitionField
from ..constants import VIDEO_OBJECT_DEFINITION_TYPE


class VideoObjectDefinitionField(ObjectDefinitionField):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/video/activity-type/video`.
        extensions (dict): See ObjectDefinitionExtensionsField.
    """

    type: VIDEO_OBJECT_DEFINITION_TYPE = VIDEO_OBJECT_DEFINITION_TYPE.__args__[0]
    extensions: Optional[ObjectDefinitionExtensionsField]


class VideoObjectField(ActivityObjectField):
    """Represents the `object` xAPI field for video statements.

    WARNING: Contains an optional name property, this is not a violation of
    conformity but goes against xAPI specification recommendations.

    Attributes:
        name (dict): Consists of the dictionary `{"en-US": <name of the video>}`.
        definition (dict): See VideoObjectDefinitionField.
    """

    name: Optional[dict[LANG_EN_US_DISPLAY, str]]
    definition: VideoObjectDefinitionField
