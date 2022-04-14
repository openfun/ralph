"""Common xAPI verb field definitions"""

from typing import Optional

from ..config import BaseModelWithConfig
from ..constants import (
    LANG_EN_US_DISPLAY,
    VERB_TERMINATED_DISPLAY,
    VERB_TERMINATED_ID,
    VERB_VIEWED_DISPLAY,
    VERB_VIEWED_ID,
)
from .common import IRI, LanguageMap


class VerbField(BaseModelWithConfig):
    """Represents the `verb` xAPI field.

    Attributes:
        id (IRI): Consists of an identifier for the verb.
        display (LanguageMap): Consists of a human readable representation of the verb.
    """

    id: IRI
    display: Optional[LanguageMap]


class ViewedVerbField(VerbField):
    """Represents the `verb` xAPI Field for the action `viewed`.

    Attributes:
       id (str): Consists of the value `http://id.tincanapi.com/verb/viewed`.
       display (dict): Consists of the dictionary `{"en-US": "viewed"}`.
    """

    id: VERB_VIEWED_ID = VERB_VIEWED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_VIEWED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_VIEWED_DISPLAY.__args__[0]
    }


class TerminatedVerbField(VerbField):
    """Represents the `verb` xAPI Field for the action `terminated`.

    Attributes:
       id (str): Consists of the value `http://adlnet.gov/expapi/verbs/terminated`.
       display (dict): Consists of the dictionary `{"en-US": "terminated"}`.
    """

    id: VERB_TERMINATED_ID = VERB_TERMINATED_ID.__args__[0]
    display: dict[LANG_EN_US_DISPLAY, VERB_TERMINATED_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: VERB_TERMINATED_DISPLAY.__args__[0]
    }
