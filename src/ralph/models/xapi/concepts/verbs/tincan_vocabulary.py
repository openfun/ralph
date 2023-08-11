"""`TinCan Vocabulary` verbs definitions."""

from typing import Dict, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class ViewedVerb(BaseXapiVerb):
    """Pydantic model for viewed `verb`.

    Attributes:
        id (str): Consists of the value `http://id.tincanapi.com/verb/viewed`.
        display (dict): Consists of the dictionary `{"en-US": "viewed"}`.
    """

    id: Literal[
        "http://id.tincanapi.com/verb/viewed"
    ] = "http://id.tincanapi.com/verb/viewed"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["viewed"]]] = None # TODO: validate that this is the behavior we want


class DownloadedVerb(BaseXapiVerb):
    """Pydantic model for downloaded `verb`.

    Attributes:
        id (str): Consists of the value `http://id.tincanapi.com/verb/downloaded`.
        display (dict): Consists of the dictionary `{"en-US": "downloaded"}`.
    """

    id: Literal[
        "http://id.tincanapi.com/verb/downloaded"
    ] = "http://id.tincanapi.com/verb/downloaded"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["downloaded"]]] = None # TODO: validate that this is the behavior we want
