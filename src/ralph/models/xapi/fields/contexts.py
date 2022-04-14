"""Common xAPI context field definitions"""

from typing import Optional, Union
from uuid import UUID

from pydantic import StrictStr

from ..config import BaseModelWithConfig
from .actors import ActorField, GroupActorField
from .common import IRI, LanguageTag
from .unnested_objects import ActivityObjectField, StatementRefObjectField


class ContextActivitiesContextField(BaseModelWithConfig):
    """Represents the `context.contextActivities` xAPI field.

    Attributes:
        parent (list): An Activity with a direct relation to the statement's Activity.
        grouping (list): An Activity with an indirect relation to the statement's
            Activity.
        category (list): An Activity used to categorize the Statement.
        other (list): A contextActivity that doesn't fit one of the other properties.
    """

    parent: Optional[Union[ActivityObjectField, list[ActivityObjectField]]]
    grouping: Optional[Union[ActivityObjectField, list[ActivityObjectField]]]
    category: Optional[Union[ActivityObjectField, list[ActivityObjectField]]]
    other: Optional[Union[ActivityObjectField, list[ActivityObjectField]]]


class ContextField(BaseModelWithConfig):
    """Represents the `context` xAPI field.

    Attributes:
        registration (UUID): The registration that the Statement is associated with.
        instructor (ActorField): The instructor that the Statement relates to.
        team (GroupActorField): The team that this Statement relates to.
        contextActivities (dict): See ContextActivitiesContextField.
        revision (str): The revision of the activity associated with this Statement.
        platform (str): The platform where the learning activity took place.
        language (LanguageTag): The language in which the experience occurred.
        statement (StatementRef): Another Statement giving context for this Statement.
        extensions (dict): Consists of an dictionary of other properties as needed.
    """

    registration: Optional[UUID]
    instructor: Optional[ActorField]
    team: Optional[GroupActorField]
    contextActivities: Optional[ContextActivitiesContextField]
    revision: Optional[StrictStr]
    platform: Optional[StrictStr]
    language: Optional[LanguageTag]
    statement: Optional[StatementRefObjectField]
    extensions: Optional[dict[IRI, Union[str, int, bool, list, dict, None]]]
