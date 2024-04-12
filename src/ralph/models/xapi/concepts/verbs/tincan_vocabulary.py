"""`TinCan Vocabulary` verbs definitions."""

import sys
from typing import Dict, Optional

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class ViewedVerb(BaseXapiVerb):
    """Pydantic model for viewed `verb`.

    Attributes:
        id (str): Consists of the value `http://id.tincanapi.com/verb/viewed`.
        display (dict): Consists of the dictionary `{"en-US": "viewed"}`.
    """

    id: Literal["http://id.tincanapi.com/verb/viewed"] = (
        "http://id.tincanapi.com/verb/viewed"
    )
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["viewed"]]] = None


class DownloadedVerb(BaseXapiVerb):
    """Pydantic model for downloaded `verb`.

    Attributes:
        id (str): Consists of the value `http://id.tincanapi.com/verb/downloaded`.
        display (dict): Consists of the dictionary `{"en-US": "downloaded"}`.
    """

    id: Literal["http://id.tincanapi.com/verb/downloaded"] = (
        "http://id.tincanapi.com/verb/downloaded"
    )
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["downloaded"]]] = None


class UnregisteredVerb(BaseXapiVerb):
    """Pydantic model for unregistered `verb`.

    Attributes:
        id (str): Consists of the value `http://id.tincanapi.com/verb/unregistered`.
        display (dict): Consists of the dictionary `{"en-US": "unregistered"}`.
    """

    id: Literal["http://id.tincanapi.com/verb/unregistered"] = (
        "http://id.tincanapi.com/verb/unregistered"
    )
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["unregistered"]]] = None
