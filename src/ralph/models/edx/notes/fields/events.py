"""Notes event field definition."""

import sys
from typing import Dict, List

from pydantic import constr

from ...base import AbstractBaseEventField

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class NotesEventField(AbstractBaseEventField):
    """Pydantic model for notes core `event` field.

    Attributes:
        component_usage_id (str): Consists of the unique identifier for the text
            component where the learner added the note.
        highlighted_content (str): Consists of the course text that the learner
            highlighted.
        note_id (str): Consists of the ID of the note.
        note_text (str): Consists of the text of the note.
        tags (list): Consists of a list of tags the learner has specified.
        truncated (list): Consists of a list of names of any truncated fields.
    """

    component_usage_id: str
    highlighted_content: str
    note_id: str
    note_text: constr(max_length=8333)
    tags: List[str] = []
    truncated: List[
        Literal["note_text", "highlighted_content", "tags", "old_note_text", "old_tags"]
    ] = []


class UIEdxCourseStudentNotesEditedEventField(NotesEventField):
    """Pydantic model for `edx.course.student.notes_edited` `event` field.

    Attributes:
        old_note_text (str): Consists of the text of the note before the learner
            edited it.
        old_tags (list): Consists of a list of tags before the learner edited it.

    """

    old_note_text: constr(max_length=8333)
    old_tags: List[str] = []


class UIEdxCourseStudentNotesNotesPageViewedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.course.student_notes.notes_page_viewed` `event` field.

    Attributes:
        view (str): Consists of the view on the Notes page that the learner
            selects. Set to `Recent Activity` value by default.
    """

    view: Literal["Recent Activity", "Search Results"] = "Recent Activity"


class UIEdxCourseStudentNotesSearchedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.course.student_notes.searched` `event` field.

    Attributes:
        number_of_results (int): Consists of the number of search results.
        search_string (str): Consists of the text of the search query.
    """

    number_of_results: int
    search_string: str


class UIEdxCourseStudentNotesUsedUnitLinkEventField(AbstractBaseEventField):
    """Pydantic model for `edx.course.student_notes.used_unit_link` `event` field.

    Attributes:
        component_usage_id (str): Consists of the unique identifier for the text
            component where the learner added the note.
        note_id (str): Consists of the ID of the note.
        view (str): Consists of the `Notes` page view that the learner was using
            when the learner selected the note.
    """

    component_usage_id: str
    note_id: str
    view: Literal["Recent Activity", "Search Results"]


class UIEdxCourseStudentNotesViewedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.course.student_notes.viewed` `event` field.

    Attributes:
        notes (list): Consists of the list of the notes identifiers values for
            any currently visible notes. Learners can add multiple notes to the
            same text.
    """

    notes: List[Dict[Literal["note_id"], str]]
