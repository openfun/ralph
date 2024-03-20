"""Notes events model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from .fields.events import (
    NotesEventField,
    UIEdxCourseStudentNotesEditedEventField,
    UIEdxCourseStudentNotesNotesPageViewedEventField,
    UIEdxCourseStudentNotesSearchedEventField,
    UIEdxCourseStudentNotesUsedUnitLinkEventField,
    UIEdxCourseStudentNotesViewedEventField,
)

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class UIEdxCourseStudentNotesAdded(BaseBrowserModel):
    """Pydantic model for `edx.course.student_notes.added` statement.

    The browser emits this event when a learner adds a note in the course.

    Attributes:
        event (NotesEventField): See NotesEventField.
        event_type (str): Consists of the value `edx.course.student_notes.added`.
        name (str): Consists of the value `edx.course.student_notes.added`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.student_notes.added"
    )

    event: Union[
        Json[NotesEventField],
        NotesEventField,
    ]
    event_type: Literal["edx.course.student_notes.added"]
    name: Literal["edx.course.student_notes.added"]


class UIEdxCourseStudentNotesDeleted(BaseBrowserModel):
    """Pydantic model for `edx.course.student_notes.deleted` statement.

    The browser emits this event when a learner deletes a note in course.

    Attributes:
        event (NotesEventField): See NotesEventField.
        event_type (str): Consists of the value `edx.course.student_notes.deleted`.
        name (str): Consists of the value `edx.course.student_notes.deleted`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.student_notes.deleted"
    )

    event: Union[
        Json[NotesEventField],
        NotesEventField,
    ]
    event_type: Literal["edx.course.student_notes.deleted"]
    name: Literal["edx.course.student_notes.deleted"]


class UIEdxCourseStudentNotesEdited(BaseBrowserModel):
    """Pydantic model for `edx.course.student_notes.edited` statement.

    The browser emits this event when a learner edits a note in course.

    Attributes:
        event (EdxCourseStudentNotesEditedEventField): See
            EdxCourseStudentNotesEditedEventField.
        event_type (str): Consists of the value `edx.course.student_notes.edited`.
        name (str): Consists of the value `edx.course.student_notes.edited`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.student_notes.edited"
    )

    event: Union[
        Json[UIEdxCourseStudentNotesEditedEventField],
        UIEdxCourseStudentNotesEditedEventField,
    ]
    event_type: Literal["edx.course.student_notes.edited"]
    name: Literal["edx.course.student_notes.edited"]


class UIEdxCourseStudentNotesNotesPageViewed(BaseBrowserModel):
    """Pydantic model for `edx.course.student_notes.notes_page_viewed` statement.

    The browser emits this event when a learner accesses the
    `Notes` page or selects a different view on the page.

    Attributes:
        event (EdxCourseStudentNotesNotesPageViewedEventField): See
            EdxCourseStudentNotesNotesPageViewedEventField.
        event_type (str): Consists of the value
            `edx.course.student_notes.notes_page_viewed`.
        name (str): Consists of the value `edx.course.student_notes.notes_page_viewed`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.student_notes.notes_page_viewed"
    )

    event: Union[
        Json[UIEdxCourseStudentNotesNotesPageViewedEventField],
        UIEdxCourseStudentNotesNotesPageViewedEventField,
    ]
    event_type: Literal["edx.course.student_notes.notes_page_viewed"]
    name: Literal["edx.course.student_notes.notes_page_viewed"]


class UIEdxCourseStudentNotesSearched(BaseBrowserModel):
    """Pydantic model for `edx.course.student_notes.searched` statement.

    The browser emits this event when a learner searches notes on the `Notes` page.

    Attributes:
        event (EdxCourseStudentNotesSearchedEventField): See
            EdxCourseStudentNotesSearchedEventField.
        event_type (str): Consists of the value `edx.course.student_notes.searched`.
        name (str): Consists of the value `edx.course.student_notes.searched`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.student_notes.searched"
    )

    event: Union[
        Json[UIEdxCourseStudentNotesSearchedEventField],
        UIEdxCourseStudentNotesSearchedEventField,
    ]
    event_type: Literal["edx.course.student_notes.searched"]
    name: Literal["edx.course.student_notes.searched"]


class UIEdxCourseStudentNotesUsedUnitLink(BaseBrowserModel):
    """Pydantic model for `edx.course.student_notes.used_unit_link` statement.

    The browser emits this event when a learner uses a note link on the `Notes`
    page to go to the `Text` component that contains that note.

    Attributes:
        event (EdxCourseStudentNotesUsedUnitLinkEventField): See
            EdxCourseStudentNotesUsedUnitLinkEventField.
        event_type (str): Consists of the value
            `edx.course.student_notes.used_unit_link`.
        name (str): Consists of the value `edx.course.student_notes.used_unit_link`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.student_notes.used_unit_link"
    )

    event: Union[
        Json[UIEdxCourseStudentNotesUsedUnitLinkEventField],
        UIEdxCourseStudentNotesUsedUnitLinkEventField,
    ]
    event_type: Literal["edx.course.student_notes.used_unit_link"]
    name: Literal["edx.course.student_notes.used_unit_link"]


class UIEdxCourseStudentNotesViewed(BaseBrowserModel):
    """Pydantic model for `edx.course.student_notes.viewed` statement.

    The browser emits this event when a learner uses a note link on the `Notes`
    page to go to the `Text` component that contains that note.

    Attributes:
        event (EdxCourseStudentNotesViewedEventField): See
            EdxCourseStudentNotesViewedEventField.
        event_type (str): Consists of the value
            `edx.course.student_notes.viewed`.
        name (str): Consists of the value `edx.course.student_notes.viewed`.
    """

    __selector__ = selector(
        event_source="browser", event_type="edx.course.student_notes.viewed"
    )

    event: Union[
        Json[UIEdxCourseStudentNotesViewedEventField],
        UIEdxCourseStudentNotesViewedEventField,
    ]
    event_type: Literal["edx.course.student_notes.viewed"]
    name: Literal["edx.course.student_notes.viewed"]
