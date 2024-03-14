"""Course Content Completion event model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.edx.course_content_completion.fields.events import (
    EdxDoneToggledEventField,
)
from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from ..server import BaseServerModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class UIEdxDoneToggled(BaseBrowserModel):
    """Pydantic model for browser `edx.done.toggled` statement.

    The browser emits this statement when the control added by the Completion
    XBlock is toggled.

    NB: both server and browser can emit this statement.

    Attributes:
        event (EdxDoneToggledEventField): See EdxDoneToggledEventField.
        event_type (str): Consists of the value `edx.done.toggled`.
        name (str): Consists either of the value `edx.done.toggled`.
    """

    __selector__ = selector(event_source="browser", event_type="edx.done.toggled")

    event: Union[
        Json[EdxDoneToggledEventField],
        EdxDoneToggledEventField,
    ]
    event_type: Literal["edx.done.toggled"]
    name: Literal["edx.done.toggled"]


class EdxDoneToggled(BaseServerModel):
    """Pydantic model for server `edx.done.toggled` statement.

    The server emits this statement when the control added by the Completion
    XBlock is toggled.

    NB: both server and browser can emit this statement.

    Attributes:
        event (EdxDoneToggledEventField): See EdxDoneToggledEventField.
        event_type (str): Consists of the value `edx.done.toggled`.
        name (str): Consists either of the value `edx.done.toggled`.
    """

    __selector__ = selector(event_source="server", event_type="edx.done.toggled")

    event: Union[
        Json[EdxDoneToggledEventField],
        EdxDoneToggledEventField,
    ]
    event_type: Literal["edx.done.toggled"]
    name: Literal["edx.done.toggled"]
