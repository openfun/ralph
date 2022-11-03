"""Video xAPI events verb fields definitions."""

from ...constants import (
    LANG_EN_US_DISPLAY,
    VERB_COMPLETED_DISPLAY,
    VERB_COMPLETED_ID,
    VERB_INITIALIZED_DISPLAY,
    VERB_INITIALIZED_ID,
    VERB_INTERACTED_DISPLAY,
    VERB_INTERACTED_ID,
    VERB_PAUSED_DISPLAY,
    VERB_PLAYED_DISPLAY,
    VERB_SEEKED_DISPLAY,
    VERB_TERMINATED_DISPLAY,
    VERB_TERMINATED_ID,
)
from ...fields.verbs import VerbField
from ..constants import VERB_VIDEO_PAUSED_ID, VERB_VIDEO_PLAYED_ID, VERB_VIDEO_SEEKED_ID


class VideoInitializedVerbField(VerbField):
    """Pydantic model for video initialized `verb` field.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/initialized`.
        display (dict): Consists of the dictionary `{"en-US": "initialized"}`.
    """

    id: VERB_INITIALIZED_ID = VERB_INITIALIZED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_INITIALIZED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_INITIALIZED_DISPLAY.__args__[0]
    }


class VideoPlayedVerbField(VerbField):
    """Pydantic model for video played `verb` field.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video/verbs/played`.
        display (dict): Consists of the dictionary `{"en-US": "played"}`.
    """

    id: VERB_VIDEO_PLAYED_ID = VERB_VIDEO_PLAYED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_PLAYED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_PLAYED_DISPLAY.__args__[0]
    }


class VideoPausedVerbField(VerbField):
    """Pydantic model for video paused `verb` field.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video/verbs/paused`.
        display (dict): Consists of the dictionary `{"en-US": "paused"}`.
    """

    id: VERB_VIDEO_PAUSED_ID = VERB_VIDEO_PAUSED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_PAUSED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_PAUSED_DISPLAY.__args__[0]
    }


class VideoSeekedVerbField(VerbField):
    """Pydantic model for video seeked `verb` field.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video/verbs/seeked`.
        display (dict): Consists of the dictionary `{"en-US": "seeked"}`.
    """

    id: VERB_VIDEO_SEEKED_ID = VERB_VIDEO_SEEKED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_SEEKED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_SEEKED_DISPLAY.__args__[0]
    }


class VideoCompletedVerbField(VerbField):
    """Pydantic model for video completed `verb` field.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/completed`.
        display (dict): Consists of the dictionary `{"en-US": "completed"}`.
    """

    id: VERB_COMPLETED_ID = VERB_COMPLETED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_COMPLETED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_COMPLETED_DISPLAY.__args__[0]
    }


class VideoTerminatedVerbField(VerbField):
    """Pydantic model for video termainated `verb` field.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/terminated`.
        display (dict): Consists of the dictionary `{"en-US": "terminated"}`.
    """

    id: VERB_TERMINATED_ID = VERB_TERMINATED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_TERMINATED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_TERMINATED_DISPLAY.__args__[0]
    }


class VideoInteractedVerbField(VerbField):
    """Pydantic model for video interacted `verb` field.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/interacted`.
        display (dict): Consists of the dictionary `{"en-US": "interacted"}`.
    """

    id: VERB_INTERACTED_ID = VERB_INTERACTED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_INTERACTED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_INTERACTED_DISPLAY.__args__[0]
    }
