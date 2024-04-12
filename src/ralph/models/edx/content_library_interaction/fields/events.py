"""Video event fields definitions."""

import sys
from typing import List, Optional

from pydantic import PositiveInt

from ...base import AbstractBaseEventField, BaseModelWithConfig

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class EdxLibraryContentBlockContentComponent(BaseModelWithConfig):
    """Pydantic model for content library interaction core `event`.`result`
    field.

    Attributes:
        descendants (list): Consists of identifiers of each part of a library
            component that contains multiple parts.
        original_usage_key (str): Consists of the ID of the component in the library.
        original_usage_version (str): Consists of the version of the component
            in the library.
        usage_key (str): Consists of the location of this component in the course.
    """  # noqa: D205

    descendants: Optional[list] = None
    original_usage_key: str
    original_usage_version: str
    usage_key: str


class ContentLibraryInteractionBaseEventField(AbstractBaseEventField):
    """Pydantic model for content library interaction core `event` field.

    Attributes:
        location (str): Consists of the ID of the randomized content block
            component.
        max_count (int): Consists of the number of library components to deliver
            specified by a course team member in Studio.
        previous_count (int): Consists of the number of components assigned to
            this student before this event. Set to `0` the first time the user
            views the randomized content block.
        result (list): Consists of the library components delivered to the user.
            See EdxLibraryContentBlockContentComponent for more information.
    """

    location: str
    max_count: PositiveInt
    previous_count: PositiveInt
    result: List[EdxLibraryContentBlockContentComponent]


class EdxLibraryContentBlockContentAssignedEventField(
    ContentLibraryInteractionBaseEventField
):
    """Pydantic model for `edx.librarycontentblock.content.assigned`.`event` field.

    Attributes:
        added (list): Consists of the library components that were delivered
            to the user for the first time. See
            EdxLibraryContentBlockContentComponent for more information.
    """

    added: List[EdxLibraryContentBlockContentComponent]


class EdxLibraryContentBlockContentRemovedEventField(
    ContentLibraryInteractionBaseEventField
):
    """Pydantic model for `edx.librarycontentblock.content.removed`.`event` field.

    Attributes:
        reason (str): Set to `overlimit` if a course team member reduces the
            Count of library components to deliver or `invalid` if the component is no
            longer included in the library, or no longer matches the settings
            specified for the randomized content block.
        removed (list): Consists of the library components that are no longer
            delivered to the user. See EdxLibraryContentBlockContentComponent
            for more information.
    """

    reason: Literal["overlimit", "invalid"]
    removed: List[EdxLibraryContentBlockContentComponent]
