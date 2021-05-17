"""Video xAPI events verb fields definitions"""

from ...base import BaseModelWithConfig
from ...constants import LANG_EN_US_DISPLAY, VERB_PLAYED_DISPLAY
from ..constants import VERB_VIDEO_PLAYED_ID


class VideoPlayedVerbField(BaseModelWithConfig):
    """Represents the `verb` field for video played xAPI statement.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video/verbs/played`.
        display (dict): Consists of the dictionary `{"en-US": "played"}`.
    """

    id: VERB_VIDEO_PLAYED_ID = VERB_VIDEO_PLAYED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_PLAYED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_PLAYED_DISPLAY.__args__[0]
    }
