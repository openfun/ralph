"""`Navy Common Reference Profile` verbs definitions."""

from typing import Dict, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class AccessedVerb(BaseXapiVerb):
    """Pydantic model for accessed `verb`.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/netc/verbs/accessed`.
        display (dict): Consists of the dictionary `{"en-US": "accessed"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/netc/verbs/accessed"
    ] = "https://w3id.org/xapi/netc/verbs/accessed"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["accessed"]]]


class UploadedVerb(BaseXapiVerb):
    """Pydantic model for uploaded `verb`.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/netc/verbs/uploaded`.
        display (dict): Consists of the dictionary `{"en-US": "uploaded"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/netc/verbs/uploaded"
    ] = "https://w3id.org/xapi/netc/verbs/uploaded"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["uploaded"]]]
