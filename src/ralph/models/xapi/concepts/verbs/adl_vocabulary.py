"""`ADL Vocabulary` verbs definitions."""

from typing import Dict, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class AskedVerb(BaseXapiVerb):
    """Pydantic model for asked `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/asked`.
        display (dict): Consists of the dictionary `{"en-US": "asked"}`.
    """

    id: Literal[
        "http://adlnet.gov/expapi/verbs/asked"
    ] = "http://adlnet.gov/expapi/verbs/asked"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["asked"]]] = None # TODO: validate that this is the behavior we want


class AnsweredVerb(BaseXapiVerb):
    """Pydantic model for answered `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/answered`.
        display (dict): Consists of the dictionary `{"en-US": "answered"}`.
    """

    id: Literal[
        "http://adlnet.gov/expapi/verbs/answered"
    ] = "http://adlnet.gov/expapi/verbs/answered"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["answered"]]] = None # TODO: validate that this is the behavior we want
