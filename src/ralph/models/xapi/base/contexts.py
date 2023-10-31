"""Base xAPI `Context` definitions."""

from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import StrictStr

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .common import IRI, LanguageTag
from .groups import BaseXapiGroup
from .unnested_objects import BaseXapiActivity, BaseXapiStatementRef


class BaseXapiContextContextActivities(BaseModelWithConfig):
    """Pydantic model for context `contextActivities` property.

    Attributes:
        parent (dict or list): An Activity with a direct relation to the statement's
            Activity.
        grouping (dict or list): An Activity with an indirect relation to the
            statement's Activity.
        category (dict or list): An Activity used to categorize the Statement.
        other (dict or list): A contextActivity that doesn't fit one of the other
            properties.
    """

    parent: Optional[Union[BaseXapiActivity, List[BaseXapiActivity]]] = None
    grouping: Optional[Union[BaseXapiActivity, List[BaseXapiActivity]]] = None
    category: Optional[Union[BaseXapiActivity, List[BaseXapiActivity]]] = None
    other: Optional[Union[BaseXapiActivity, List[BaseXapiActivity]]] = None


class BaseXapiContext(BaseModelWithConfig):
    """Pydantic model for `context` property.

    Attributes:
        registration (UUID): The registration that the Statement is associated with.
        instructor (dict): The instructor that the Statement relates to.
        team (dict): The team that this Statement relates to.
        contextActivities (dict): See BaseXapiContextContextActivities.
        revision (str): The revision of the activity associated with this Statement.
        platform (str): The platform where the learning activity took place.
        language (dict): The language in which the experience occurred.
        statement (dict): Another Statement giving context for this Statement.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    registration: Optional[UUID] = None
    instructor: Optional[BaseXapiAgent] = None
    team: Optional[BaseXapiGroup] = None
    contextActivities: Optional[BaseXapiContextContextActivities] = None
    revision: Optional[StrictStr] = None
    platform: Optional[StrictStr] = None
    language: Optional[LanguageTag] = None
    statement: Optional[BaseXapiStatementRef] = None
    extensions: Optional[Dict[IRI, Union[str, int, bool, list, dict, None]]] = None
