"""Common xAPI verb field definitions"""

from typing import Literal

from ..config import BaseModelWithConfig
from ..constants import (
    LANG_EN_US_DISPLAY,
    VERB_TERMINATED_DISPLAY,
    VERB_TERMINATED_ID,
    VERB_VIEWED_DISPLAY,
    VERB_VIEWED_ID,
)


class ViewedVerbField(BaseModelWithConfig):
    """Represents the `verb` xAPI Field for the action `viewed`.

    Attributes:
       id (str): Consists of the value `http://id.tincanapi.com/verb/viewed`.
       display (dict): Consists of the dictionary `{"en": "viewed"}`.
    """

    id: Literal[VERB_VIEWED_ID] = VERB_VIEWED_ID
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal[VERB_VIEWED_DISPLAY]] = {
        LANG_EN_US_DISPLAY: VERB_VIEWED_DISPLAY
    }


class TerminatedVerbField(BaseModelWithConfig):
    """Represents the `verb` xAPI Field for the action `terminated`.

    Attributes:
       id (str): Consists of the value `http://adlnet.gov/expapi/verbs/terminated`.
       display (dict): Consists of the dictionary `{"en": "terminated"}`.
    """

    id: Literal[VERB_TERMINATED_ID] = VERB_TERMINATED_ID
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal[VERB_TERMINATED_DISPLAY]] = {
        LANG_EN_US_DISPLAY: VERB_TERMINATED_DISPLAY
    }
