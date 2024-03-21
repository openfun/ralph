"""Peer instruction event field definition."""

import sys
from typing import List, Union

from pydantic import constr, validator

from ...base import AbstractBaseEventField

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class TeamsEventField(AbstractBaseEventField):
    """Pydantic model for teams core `event` field.

    Attributes:
        team_id (str): Consists of the identifier of the team.
    """

    team_id: str


class EdxTeamChangedEventField(TeamsEventField):
    """Pydantic model for `edx.team.changed` `event` field.

    Attributes:
        field (str): Consists of the name of the field within the team’s details
            that was modified.
        new (str): Consists of the value of the field after the modification. If
            longer than 1250 characters, it is truncated and suffixed with `...`.
        old (str): Consists of the value of the field before the modification. If
            longer than 1250 characters, it is truncated and suffixed with `...`.
        truncated (list): Consists of the truncated values of `new` and `old` if
            the values are longer than 1250.
    """

    field: str
    new: constr(max_length=1250)
    old: constr(max_length=1250)
    truncated: List[str]

    @validator("truncated")
    def check_truncated_length(cls, v):
        """Check length of truncated field."""
        if not len(v) <= 2:  # noqa: PLR2004
            raise ValueError("truncated length must be lower than 2")
        return v


class EdxTeamLearnerAddedEventField(TeamsEventField):
    """Pydantic model for `edx.team.learner_added` `event` field.

    Attributes:
        add_method (str): Consists of the method by which the user joined the
            team. Possible values are `added_on_create`, `joined_from_team_view`
            or `added_by_another_user`.
        user_id (str): Consists of the identifier for the user who joined or was
            added to the team.
    """

    add_method: Literal[
        "added_on_create", "joined_from_team_view", "added_by_another_user"
    ]
    user_id: str


class EdxTeamLearnerRemovedEventField(TeamsEventField):
    """Pydantic model for `edx.team.learner_removed` `event` field.

    Attributes:
        remove_method (str): Consists of the method by which the user was
            removed from the team. Possible values are `self_removal`, `team_deleted`,
            or `removed_by_admin`.
        user_id (str): Consists of the identifier for the user who left or was
            removed from the team.
    """

    remove_method: Literal["self_removal", "team_deleted", "removed_by_admin"]
    user_id: str


class EdxTeamPageViewedEventField(TeamsEventField):
    """Pydantic model for `edx.team.page_viewed` `event` field.

    Attributes:
        page_name (str): Consists of the name of the page that was viewed.
            Possible values are: `browse`, `edit-team`, `my-teams`, `new-team`,
            `search-teams`, `single-team` and `single-topic`.
        topic_id (str): Consists of the identifier of the topic related to the
            page that was viewed.
    """

    page_name: Literal[
        "browse",
        "edit-team",
        "my-teams",
        "new-team",
        "search-teams",
        "single-team",
        "single-topic",
    ]
    topic_id: Union[str, Literal["null"]]


class EdxTeamSearchedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.team.searched` `event` field.

    Attributes:
        number_of_results (int): Consists of the number of results that matched
            the search text.
        search_text (str): Consists of the text or keywords used in the search.
        topic_id (str): Consists of the identifier for the topic under which
            this search for teams was performed.
    """

    number_of_results: int
    search_text: str
    topic_id: str
