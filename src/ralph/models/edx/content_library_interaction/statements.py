"""Content library interaction event model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.edx.content_library_interaction.fields.events import (
    EdxLibraryContentBlockContentAssignedEventField,
    EdxLibraryContentBlockContentRemovedEventField,
)
from ralph.models.selector import selector

from ..server import BaseServerModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class EdxLibraryContentBlockContentAssigned(BaseServerModel):
    """Pydantic model for `edx.librarycontentblock.content.assigned` statement.

    The server emits this statement the first time that content from a
    randomized content block is delivered to a user.

    Attributes:
        event (EdxLibraryContentBlockContentAssignedEventField): See
            EdxLibraryContentBlockContentAssignedEventField.
        event_type (str): Consists of the value
            `edx.librarycontentblock.content.assigned`.
        name (str): Consists either of the value
            `edx.librarycontentblock.content.assigned`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.librarycontentblock.content.assigned"
    )

    event: Union[
        Json[EdxLibraryContentBlockContentAssignedEventField],
        EdxLibraryContentBlockContentAssignedEventField,
    ]
    event_type: Literal["edx.librarycontentblock.content.assigned"]
    name: Literal["edx.librarycontentblock.content.assigned"]


class EdxLibraryContentBlockContentRemoved(BaseServerModel):
    """Pydantic model for `edx.librarycontentblock.content.removed` statement.

    The server emits this statement the first time that content from a
    randomized content block is delivered to a user.

    Attributes:
        event (EdxLibraryContentBlockContentRemovedEventField): See
            EdxLibraryContentBlockContentRemovedEventField.
        event_type (str): Consists of the value
            `edx.librarycontentblock.content.removed`.
        name (str): Consists either of the value
            `edx.librarycontentblock.content.removed`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.librarycontentblock.content.removed"
    )

    event: Union[
        Json[EdxLibraryContentBlockContentRemovedEventField],
        EdxLibraryContentBlockContentRemovedEventField,
    ]
    event_type: Literal["edx.librarycontentblock.content.removed"]
    name: Literal["edx.librarycontentblock.content.removed"]
