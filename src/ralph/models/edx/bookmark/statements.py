"""Bookmark event model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.edx.bookmark.fields.events import (
    EdxBookmarkAddedEventField,
    EdxBookmarkBaseEventField,
    EdxBookmarkListedEventField,
    EdxBookmarkRemovedEventField,
    UIEdxCourseToolAccessedEventField,
)
from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from ..server import BaseServerModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class UIEdxBookmarkAccessed(BaseBrowserModel):
    """Pydantic model for `edx.bookmark.accessed` statement.

    The browser emits this statement when a user accesses a bookmark by
    selecting a link on the `My Bookmarks` page in the LMS.

    Attributes:
        event (EdxBookmarkBaseEventField): See EdxBookmarkBaseEventField.
        event_type (str): Consists of the value `edx.bookmark.accessed`.
        name (str): Consists either of the value `edx.bookmark.accessed`.
    """

    __selector__ = selector(event_source="browser", event_type="edx.bookmark.accessed")

    event: Union[
        Json[EdxBookmarkBaseEventField],
        EdxBookmarkBaseEventField,
    ]
    event_type: Literal["edx.bookmark.accessed"]
    name: Literal["edx.bookmark.accessed"]


class EdxBookmarkAdded(BaseServerModel):
    """Pydantic model for `edx.bookmark.added` statement.

    The server emits this statement when a user bookmarks a page in the course.

    Attributes:
        event (EdxBookmarkAddedEventField): See EdxBookmarkAddedEventField.
        event_type (str): Consists of the value `edx.bookmark.added`.
        name (str): Consists either of the value `edx.bookmark.added`.
    """

    __selector__ = selector(event_source="server", event_type="edx.bookmark.added")

    event: Union[
        Json[EdxBookmarkAddedEventField],
        EdxBookmarkAddedEventField,
    ]
    event_type: Literal["edx.bookmark.added"]
    name: Literal["edx.bookmark.added"]


class EdxBookmarkListed(BaseServerModel):
    """Pydantic model for `edx.bookmark.listed` statement.

    The server emits this event when a user clicks <kbd>Bookmarks</kbd> under
    the `Course Tools` heading in the LMS to view the list of previously
    bookmarked pages.

    Attributes:
        event (EdxBookmarkListedEventField): See EdxBookmarkListedEventField.
        event_type (str): Consists of the value `edx.bookmark.listed`.
        name (str): Consists either of the value `edx.bookmark.listed`.
    """

    __selector__ = selector(event_source="server", event_type="edx.bookmark.listed")

    event: Union[
        Json[EdxBookmarkListedEventField],
        EdxBookmarkListedEventField,
    ]
    event_type: Literal["edx.bookmark.listed"]
    name: Literal["edx.bookmark.listed"]


class EdxBookmarkRemoved(BaseServerModel):
    """Pydantic model for `edx.bookmark.removed` statement.

    The server emits this statement when a user removes a bookmark from a page.

    Attributes:
        event (EdxBookmarkRemovedEventField): See EdxBookmarkRemovedEventField.
        event_type (str): Consists of the value `edx.bookmark.removed`.
        name (str): Consists either of the value `edx.bookmark.removed`.
    """

    __selector__ = selector(event_source="server", event_type="edx.bookmark.removed")

    event: Union[
        Json[EdxBookmarkRemovedEventField],
        EdxBookmarkRemovedEventField,
    ]
    event_type: Literal["edx.bookmark.removed"]
    name: Literal["edx.bookmark.removed"]


class UIEdxCourseToolAccessed(BaseBrowserModel):
    """Pydantic model for `edx.course.tool.accessed` statement.

    The browser emits this statement when a user clicks one
    of the links under the Course Tools heading in the LMS, such as
    <kbd>Bookmarks</kbd>, <kbd>Reviews</kbd>, or <kbd>Updates</kbd>.

    Attributes:
        event (EdxCourseToolAccessedEventField): See EdxCourseToolAccessedEventField.
        event_type (str): Consists of the value `edx.course.tool.accessed`.
        name (str): Consists either of the value `edx.course.tool.accessed`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.tool.accessed"
    )

    event: Union[
        Json[UIEdxCourseToolAccessedEventField],
        UIEdxCourseToolAccessedEventField,
    ]
    event_type: Literal["edx.course.tool.accessed"]
    name: Literal["edx.course.tool.accessed"]
