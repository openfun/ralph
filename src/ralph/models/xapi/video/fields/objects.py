"""Video xAPI events object fields definitions"""

from typing import Literal, Optional

from ralph.models.xapi.config import BaseModelWithConfig

from ...constants import LANG_EN_US_DISPLAY
from ...fields.objects import ObjectDefinitionExtensionsField, ObjectField
from ..constants import VIDEO_OBJECT_DEFINITION_TYPE


class VideoObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    WARNING: It doesn't include the recommended `description` field nor the optional `moreInfo`,
    `Interaction properties` and `extensions` fields.

    Attributes:
       name (dict): Consists of the dictionary `{"en-US": <name of the video>}`.
       type (str): Consists of the value `https://w3id.org/xapi/video/activity-type/video`.
    """

    name: Optional[dict[LANG_EN_US_DISPLAY, str]]
    type: VIDEO_OBJECT_DEFINITION_TYPE = VIDEO_OBJECT_DEFINITION_TYPE.__args__[0]
    extensions: Optional[ObjectDefinitionExtensionsField]


class VideoObjectField(ObjectField):
    """Represents the `object` xAPI field for video statements.

    Attributes:
        definition (VideoObjectDefinitionField): See VideoObjectDefinitionField.
        objectType: Consists of the value "Activity".
    """

    name: Optional[dict[LANG_EN_US_DISPLAY, str]]
    definition: VideoObjectDefinitionField
    objectType: Optional[Literal["Activity"]]
