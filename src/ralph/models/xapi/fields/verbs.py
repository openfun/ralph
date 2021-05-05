"""Common xAPI verb field definitions"""

from ..config import BaseModelWithConfig
from ..constants import (
    LANG_EN_DISPLAY,
    VERB_TERMINATED_DISPLAY,
    VERB_TERMINATED_ID,
    VERB_VIEWED_DISPLAY,
    VERB_VIEWED_ID,
)


class ViewedVerbField(BaseModelWithConfig):
    """Represents the `verb` xAPI Field for page viewed xAPI statement.

    Attributes:
       id (str): Consists of the value `http://id.tincanapi.com/verb/viewed`.
       display (dict): Consists of the dictionary `{"en": "viewed"}`.
    """

    id: VERB_VIEWED_ID = VERB_VIEWED_ID.__args__[0]
    display: dict[LANG_EN_DISPLAY, VERB_VIEWED_DISPLAY] = {
        LANG_EN_DISPLAY.__args__[0]: VERB_VIEWED_DISPLAY.__args__[0]
    }


class TerminatedVerbField(BaseModelWithConfig):
    """Represents the `verb` xAPI Field for page terminated xAPI statement.

    Attributes:
       id (str): Consists of the value `http://adlnet.gov/expapi/verbs/terminated`.
       display (dict): Consists of the dictionary `{"en": "terminated"}`.
    """

    id: VERB_TERMINATED_ID = VERB_TERMINATED_ID.__args__[0]
    display: dict[LANG_EN_DISPLAY, VERB_TERMINATED_DISPLAY] = {
        LANG_EN_DISPLAY.__args__[0]: VERB_TERMINATED_DISPLAY.__args__[0]
    }
