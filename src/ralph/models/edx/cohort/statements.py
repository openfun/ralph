"""Cohort events model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.selector import selector

from ..server import BaseServerModel
from .fields.events import CohortBaseEventField, CohortUserBaseEventField

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class EdxCohortCreated(BaseServerModel):
    """Pydantic model for `edx.cohort.created` statement.

    The server emits this statement when a course team or the system creates a cohort.

    Attributes:
        event_type (str): Consists of the value `edx.cohort.created`.
        name (str): Consists of the value `edx.cohort.created`.
    """

    __selector__ = selector(event_source="server", event_type="edx.cohort.created")

    event: Union[
        Json[CohortBaseEventField],
        CohortBaseEventField,
    ]
    event_type: Literal["edx.cohort.created"]
    name: Literal["edx.cohort.created"]


class EdxCohortUserAdded(BaseServerModel):
    """Pydantic model for `edx.cohort.user_added` statement.

    The server emits this statement when a user is added to a cohort.

    Attributes:
        event_type (str): Consists of the value `edx.cohort.user_added`.
        name (str): Consists of the value `edx.cohort.user_added`.
    """

    __selector__ = selector(event_source="server", event_type="edx.cohort.user_added")

    event: Union[
        Json[CohortUserBaseEventField],
        CohortUserBaseEventField,
    ]
    event_type: Literal["edx.cohort.user_added"]
    name: Literal["edx.cohort.user_added"]


class EdxCohortUserRemoved(BaseServerModel):
    """Pydantic model for `edx.cohort.user_removed` statement.

    The server emits this statement when a course team member selects
    <kbd>Instructor</kbd> in the LMS to change the cohort assignment of a
    learner on the instructor dashboard.

    Attributes:
        event_type (str): Consists of the value `edx.cohort.user_removed`.
        name (str): Consists of the value `edx.cohort.user_removed`.
    """

    __selector__ = selector(event_source="server", event_type="edx.cohort.user_removed")

    event: Union[
        Json[CohortUserBaseEventField],
        CohortUserBaseEventField,
    ]
    event_type: Literal["edx.cohort.user_removed"]
    name: Literal["edx.cohort.user_removed"]
