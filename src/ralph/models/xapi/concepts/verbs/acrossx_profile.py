"""`AcrossX Profile` verbs definitions."""

import sys
from typing import Dict, Optional

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class PostedVerb(BaseXapiVerb):
    """Pydantic model for posted `verb`.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/acrossx/verbs/posted`.
        display (dict): Consists of the dictionary `{"en-US": "posted"}`.
    """

    id: Literal["https://w3id.org/xapi/acrossx/verbs/posted"] = (
        "https://w3id.org/xapi/acrossx/verbs/posted"
    )
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["posted"]]]
