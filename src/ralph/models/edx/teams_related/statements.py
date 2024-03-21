"""Teams-related events model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.selector import selector

from ..server import BaseServerModel
from .fields.events import (
    EdxTeamChangedEventField,
    EdxTeamLearnerAddedEventField,
    EdxTeamLearnerRemovedEventField,
    EdxTeamPageViewedEventField,
    EdxTeamSearchedEventField,
    TeamsEventField,
)

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class EdxTeamActivityUpdated(BaseServerModel):
    """Pydantic model for `edx.team.activity_updated` statement.

    The server emits this event when activity has occurred on a team.

    Attributes:
        event_type (str): Consists of the value `edx.team.activity_updated`.
        name (str): Consists of the value `edx.team.activity_updated`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.team.activity_updated"
    )

    event: Union[
        Json[TeamsEventField],
        TeamsEventField,
    ]
    event_type: Literal["edx.team.activity_updated"]
    name: Literal["edx.team.activity_updated"]


class EdxTeamChanged(BaseServerModel):
    """Pydantic model for `edx.team.changed` statement.

    The server emits this event when a team’s information is edited and for each
    modification.

    Attributes:
        event_type (str): Consists of the value `edx.team.changed`.
        name (str): Consists of the value `edx.team.changed`.
    """

    __selector__ = selector(event_source="server", event_type="edx.team.changed")

    event: Union[
        Json[EdxTeamChangedEventField],
        EdxTeamChangedEventField,
    ]
    event_type: Literal["edx.team.changed"]
    name: Literal["edx.team.changed"]


class EdxTeamCreated(BaseServerModel):
    """Pydantic model for `edx.team.created` statement.

    The server emits this event when a team is created.

    Attributes:
        event_type (str): Consists of the value `edx.team.created`.
        name (str): Consists of the value `edx.team.created`.
    """

    __selector__ = selector(event_source="server", event_type="edx.team.created")

    event: Union[
        Json[TeamsEventField],
        TeamsEventField,
    ]
    event_type: Literal["edx.team.created"]
    name: Literal["edx.team.created"]


class EdxTeamDeleted(BaseServerModel):
    """Pydantic model for `edx.team.deleted` statement.

    The server emits this event when a team is deleted.

    Attributes:
        event_type (str): Consists of the value `edx.team.deleted`.
        name (str): Consists of the value `edx.team.deleted`.
    """

    __selector__ = selector(event_source="server", event_type="edx.team.deleted")

    event: Union[
        Json[TeamsEventField],
        TeamsEventField,
    ]
    event_type: Literal["edx.team.deleted"]
    name: Literal["edx.team.deleted"]


class EdxTeamLearnerAdded(BaseServerModel):
    """Pydantic model for `edx.team.learner_added` statement.

    The server emits this event when a user joins a team or is added by someone else.

    Attributes:
        event_type (str): Consists of the value `edx.team.learner_added`.
        name (str): Consists of the value `edx.team.learner_added`.
    """

    __selector__ = selector(event_source="server", event_type="edx.team.learner_added")

    event: Union[
        Json[EdxTeamLearnerAddedEventField],
        EdxTeamLearnerAddedEventField,
    ]
    event_type: Literal["edx.team.learner_added"]
    name: Literal["edx.team.learner_added"]


class EdxTeamLearnerRemoved(BaseServerModel):
    """Pydantic model for `edx.team.learner_removed` statement.

    The server emits this event wWhen a user leaves a team or is removed by
    someone else.

    Attributes:
        event_type (str): Consists of the value `edx.team.learner_removed`.
        name (str): Consists of the value `edx.team.learner_removed`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.team.learner_removed"
    )

    event: Union[
        Json[EdxTeamLearnerRemovedEventField],
        EdxTeamLearnerRemovedEventField,
    ]
    event_type: Literal["edx.team.learner_removed"]
    name: Literal["edx.team.learner_removed"]


class EdxTeamPageViewed(BaseServerModel):
    """Pydantic model for `edx.team.page_viewed` statement.

    The server emits this event when a user leaves a team or is removed by
    someone else.

    Attributes:
        event_type (str): Consists of the value `edx.team.page_viewed`.
        name (str): Consists of the value `edx.team.page_viewed`.
    """

    __selector__ = selector(event_source="server", event_type="edx.team.page_viewed")

    event: Union[
        Json[EdxTeamPageViewedEventField],
        EdxTeamPageViewedEventField,
    ]
    event_type: Literal["edx.team.page_viewed"]
    name: Literal["edx.team.page_viewed"]


class EdxTeamSearched(BaseServerModel):
    """Pydantic model for `edx.team.searched` statement.

    The server emits this event when a user performs a search for teams from the
    topic view under the `Teams` page of the courseware.

    Attributes:
        event_type (str): Consists of the value `edx.team.searched`.
        name (str): Consists of the value `edx.team.searched`.
    """

    __selector__ = selector(event_source="server", event_type="edx.team.searched")

    event: Union[
        Json[EdxTeamSearchedEventField],
        EdxTeamSearchedEventField,
    ]
    event_type: Literal["edx.team.searched"]
    name: Literal["edx.team.searched"]
