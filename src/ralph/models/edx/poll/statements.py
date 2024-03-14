"""Poll event model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.edx.poll.fields.events import XBlockPollSubmittedEventField
from ralph.models.selector import selector

from ..server import BaseServerModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class XBlockPollSubmitted(BaseServerModel):
    """Pydantic model for `xblock.poll.submitted` statement.

    The server emits this statement when a user submits a response to a poll.

    Attributes:
        event (XBlockPollSubmittedEventField): See XBlockPollSubmittedEventField.
        event_type (str): Consists of the value `xblock.poll.submitted`.
        name (str): Consists either of the value `xblock.poll.submitted`.
    """

    __selector__ = selector(event_source="server", event_type="xblock.poll.submitted")

    event: Union[
        Json[XBlockPollSubmittedEventField],
        XBlockPollSubmittedEventField,
    ]
    event_type: Literal["xblock.poll.submitted"]
    name: Literal["xblock.poll.submitted"]


class XBlockPollViewResults(BaseServerModel):
    """Pydantic model for `xblock.poll.view_results` statement.

    The server emits this statement when a tally of poll answers is displayed to a user.

    Attributes:
        event_type (str): Consists of the value `xblock.poll.view_results`.
        name (str): Consists either of the value `xblock.poll.view_results`.
    """

    __selector__ = selector(
        event_source="server", event_type="xblock.poll.view_results"
    )

    event_type: Literal["xblock.poll.view_results"]
    name: Literal["xblock.poll.view_results"]
