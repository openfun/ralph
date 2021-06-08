"""Video xAPI events object fields definitions"""

from typing import Literal, Optional

from ralph.models.xapi.config import BaseModelWithConfig

from ...constants import ACTIVITY_PAGE_DISPLAY, LANG_EN_US_DISPLAY
from ...fields.objects import ObjectField
from ..constants import VIDEO_OBJECT_DEFINITION_TYPE


class VideoObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    WARNING: It doesn't include the recommended `description` field nor the optional `moreInfo`,
    `Interaction properties` and `extensions` fields.

    Attributes:
       name (dict): Consists of the dictionary `{"en-US": "page"}`.
       type (str): Consists of the value `https://w3id.org/xapi/video/activity-type/video`.
    """

    name: dict[Literal[LANG_EN_US_DISPLAY], Literal[ACTIVITY_PAGE_DISPLAY]] = {
        LANG_EN_US_DISPLAY: ACTIVITY_PAGE_DISPLAY
    }
    type: Literal[VIDEO_OBJECT_DEFINITION_TYPE] = VIDEO_OBJECT_DEFINITION_TYPE


class VideoObjectField(ObjectField):
    """Represents the `object` xAPI field for video statements.

    Attributes:
        definition (VideoObjectDefinitionField): See VideoObjectDefinitionField.
        objectType: Consists of the value "Activity".
    """

    definitions: VideoObjectDefinitionField
    objectType: Optional[Literal["Activity"]]
