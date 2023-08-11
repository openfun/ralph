"""`Virtual classroom` verbs definitions."""

from typing import Dict, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class MutedVerb(BaseXapiVerb):
    """Pydantic model for muted `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/muted`.
        display (dict): Consists of the dictionary `{"en-US": "muted"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/muted"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/muted"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["muted"]]] = None # TODO: validate that this is the behavior we want


class UnmutedVerb(BaseXapiVerb):
    """Pydantic model for unmuted `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/unmuted`.
        display (dict): Consists of the dictionary `{"en-US": "unmuted"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/unmuted"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/unmuted"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["unmuted"]]] = None # TODO: validate that this is the behavior we want


class StartedCameraVerb(BaseXapiVerb):
    """Pydantic model for started camera `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/started-camera`.
        display (dict): Consists of the dictionary `{"en-US": "started camera"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/started-camera"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/started-camera"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["started camera"]]] = None # TODO: validate that this is the behavior we want


class StoppedCameraVerb(BaseXapiVerb):
    """Pydantic model for stopped camera `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera`.
        display (dict): Consists of the dictionary `{"en-US": "stopped camera"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["stopped camera"]]] = None # TODO: validate that this is the behavior we want


class SharedScreenVerb(BaseXapiVerb):
    """Pydantic model for shared screen `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/shared-screen`.
        display (dict): Consists of the dictionary `{"en-US": "shared screen"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/shared-screen"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/shared-screen"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["shared screen"]]] = None # TODO: validate that this is the behavior we want


class UnsharedScreenVerb(BaseXapiVerb):
    """Pydantic model for unshared screen `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen`.
        display (dict): Consists of the dictionary `{"en-US": "unshared screen"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["unshared screen"]]] = None # TODO: validate that this is the behavior we want


class RaisedHandVerb(BaseXapiVerb):
    """Pydantic model for raised hand `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/raised-hand`.
        display (dict): Consists of the dictionary `{"en-US": "raised hand"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/raised-hand"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/raised-hand"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["raised hand"]]] = None # TODO: validate that this is the behavior we want


class LoweredHandVerb(BaseXapiVerb):
    """Pydantic model for lowered hand `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand`.
        display (dict): Consists of the dictionary `{"en-US": "lowered hand"}`.
    """

    id: Literal[
        "https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand"
    ] = "https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand"
    display: Optional[Dict[Literal[LANG_EN_US_DISPLAY], Literal["lowered hand"]]] = None # TODO: validate that this is the behavior we want
