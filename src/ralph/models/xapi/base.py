"""Base xAPI model definition"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import constr, root_validator

from .config import BaseModelWithConfig
from .fields.actors import ActorField
from .fields.attachments import AttachmentField
from .fields.contexts import ContextField
from .fields.objects import ObjectField
from .fields.results import ResultField
from .fields.verbs import VerbField


class BaseXapiModel(BaseModelWithConfig):
    """Pydantic model for base statements.

    Attributes:
        id (UUID): Consists of a generated UUID string from the source event string.
        actor (ActorField): Consists of a definition of who performed the action.
        verb (VerbField): Consists of the action between an Actor and an Activity.
        object (ObjectField): Consists of a definition of the thing that was acted on.
        result (ResultField): Consists of the outcome related to the Statement.
        context (ContextField): Consists of contextual information for the Statement.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
        stored (datetime): Consists of the timestamp of when the event was recorded.
        authority (ActorField): Consists of the Actor asserting this Statement is true.
        version (str): Consists of the associated xAPI version of the Statement.
        attachments (list): Consists of a list of Attachments.
    """

    id: Optional[UUID]
    actor: ActorField
    verb: VerbField
    object: ObjectField
    result: Optional[ResultField]
    context: Optional[ContextField]
    timestamp: Optional[datetime]
    stored: Optional[datetime]
    authority: Optional[ActorField]
    version: constr(regex=r"^1\.0\.[0-9]+$") = "1.0.0"  # noqa:F722
    attachments: Optional[list[AttachmentField]]

    @root_validator(pre=True)
    @classmethod
    def check_abscence_of_empty_and_invalid_values(cls, values):
        """Checks the model for empty and invalid values.

        Checks that the `context` field contains `platform` and `revision` fields
        only if the `object.objectType` property is equal to `Activity`.
        """

        for field, value in list(values.items()):
            if value in [None, "", {}]:
                raise ValueError(f"{field}: invalid empty value")
            if isinstance(value, dict) and field != "extensions":
                cls.check_abscence_of_empty_and_invalid_values(value)

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
