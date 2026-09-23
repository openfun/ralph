"""Base xAPI `Statement` definitions."""

from datetime import datetime
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import StringConstraints, ValidationError, model_validator
from pydantic_core import InitErrorDetails, PydanticCustomError
from typing_extensions import Annotated

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

    id: Optional[UUID] = None
    actor: Union[BaseXapiAgent, BaseXapiGroup]
    verb: BaseXapiVerb
    object: BaseXapiObject
    result: Optional[BaseXapiResult] = None
    context: Optional[BaseXapiContext] = None
    timestamp: Optional[datetime] = None
    stored: Optional[datetime] = None
    authority: Optional[Union[BaseXapiAgent, BaseXapiGroup]] = None
    version: Annotated[str, StringConstraints(pattern=r"^1\.0\.[0-9]+$")] = "1.0.0"
    attachments: Optional[List[BaseXapiAttachment]] = None

    @model_validator(mode="before")
    @classmethod
    def check_absence_of_empty_and_invalid_values(cls, values: Any) -> Any:
        """Check the model for empty and invalid values.

        Check that the `context` field contains `platform` and `revision` fields
        only if the `object.objectType` property is equal to `Activity`.
        """

        def _is_empty_value(v) -> bool:
            return v in [None, "", {}]

        def _check_absence_of_empty_values(
            _values: Any, loc: tuple[Union[int, str], ...]
        ) -> Any:
            for field, value in list(_values.items()):
                if _is_empty_value(value):
                    raise ValidationError.from_exception_data(
                        "XapiEmptyValueError",
                        [
                            InitErrorDetails(
                                type=PydanticCustomError(
                                    "no_empty_value",
                                    "Statements may not contain empty values "
                                    "except inside Extensions.",
                                ),
                                loc=loc + (field,),
                                input=value,
                            )
                        ],
                    )
                if isinstance(value, dict) and field != "extensions":
                    _check_absence_of_empty_values(value, loc + (field,))

        _check_absence_of_empty_values(values, ())

        context = dict(values.get("context", {}))
        if context:
            platform = context.get("platform", {})
            revision = context.get("revision", {})
            object_type = dict(values["object"]).get("objectType", "Activity")
            if (platform or revision) and object_type != "Activity":
                raise ValidationError.from_exception_data(
                    "XapiInvalidContextError",
                    [
                        InitErrorDetails(
                            type=PydanticCustomError(
                                "invalid_context",
                                "revision and platform properties can only be used "
                                "if the Statement's Object is an Activity",
                            ),
                            loc=("context",),
                            input=context,
                        )
                    ],
                )
        return values
