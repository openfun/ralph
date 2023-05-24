"""Base xAPI `Statement` definitions."""

from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import constr, root_validator

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .attachments import BaseXapiAttachment
from .contexts import BaseXapiContext
from .groups import BaseXapiGroup
from .objects import BaseXapiObject
from .results import BaseXapiResult
from .verbs import BaseXapiVerb


class BaseXapiStatement(BaseModelWithConfig):
    """Pydantic model for base xAPI statements.

    Attributes:
        id (UUID): Consists of a generated UUID string from the source event string.
        actor (dict): Consists of a definition of who performed the action.
        verb (dict): Consists of the action between an Actor and an Activity.
        object (dict): Consists of a definition of the thing that was acted on.
        result (dict): Consists of the outcome related to the Statement.
        context (dict): Consists of contextual information for the Statement.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
        stored (datetime): Consists of the timestamp of when the event was recorded.
        authority (dict): Consists of the Actor asserting this Statement is true.
        version (str): Consists of the associated xAPI version of the Statement.
        attachments (list): Consists of a list of attachments.
    """

    id: Optional[UUID]
    actor: Union[BaseXapiAgent, BaseXapiGroup]
    verb: BaseXapiVerb
    object: BaseXapiObject
    result: Optional[BaseXapiResult]
    context: Optional[BaseXapiContext]
    timestamp: Optional[datetime]
    stored: Optional[datetime]
    authority: Optional[Union[BaseXapiAgent, BaseXapiGroup]]
    version: constr(regex=r"^1\.0\.[0-9]+$") = "1.0.0"  # noqa:F722
    attachments: Optional[List[BaseXapiAttachment]]

    @root_validator(pre=True)
    @classmethod
    def check_absence_of_empty_and_invalid_values(cls, values: Any) -> Any:
        """Check the model for empty and invalid values.

        Check that the `context` field contains `platform` and `revision` fields
        only if the `object.objectType` property is equal to `Activity`.
        """
        for field, value in list(values.items()):
            if value in [None, "", {}]:
                raise ValueError(f"{field}: invalid empty value")
            if isinstance(value, dict) and field != "extensions":
                cls.check_absence_of_empty_and_invalid_values(value)

        context = dict(values.get("context", {}))
        if context:
            platform = context.get("platform", {})
            revision = context.get("revision", {})
            object_type = dict(values["object"]).get("objectType", "Activity")
            if (platform or revision) and object_type != "Activity":
                raise ValueError(
                    "revision and platform properties can only be used if the "
                    "Statement's Object is an Activity"
                )
        return values
