"""`Activity streams vocabulary` verbs definitions."""

import sys
from typing import Dict, Optional

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class JoinVerb(BaseXapiVerb):
    """Pydantic model for join verb.

    Attributes:
        id (str): Consists of the value `http://activitystrea.ms/join`.
        display (dict): Consists of the dictionary `{"en-US": "joined"}`.
    """

    id: Literal["http://activitystrea.ms/join"] = "http://activitystrea.ms/join"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["joined"]]] = None


class LeaveVerb(BaseXapiVerb):
    """Pydantic model for leave `verb`.

    Attributes:
        id (str): Consists of the value `http://activitystrea.ms/leave`.
        display (dict): Consists of the dictionary `{"en-US": "left"}`.
    """

    id: Literal["http://activitystrea.ms/leave"] = "http://activitystrea.ms/leave"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["left"]]] = None
