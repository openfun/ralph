"""API-specific data models definition.

Allows to be exactly as lax as we want when it comes to exact object shape and
validation.
"""

from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.xapi.base.agents import BaseXapiAgent
from ..models.xapi.base.groups import BaseXapiGroup


class ErrorDetail(BaseModel):
    """Pydantic model for errors raised detail.

    Type for return value for errors raised in API endpoints.
    Useful for OpenAPI documentation generation.
    """

    detail: str


class BaseModelWithLaxConfig(BaseModel):
    """Pydantic base model with lax configuration.

    Common base lax model to perform light input validation as
    we receive statements through the API.
    """

    model_config = ConfigDict(extra="allow", coerce_numbers_to_str=True)


class LaxObjectField(BaseModelWithLaxConfig):
    """Pydantic model for lax `object` field.

    Lightest definition of an object field compliant to the specification.
    """

    id: str


class LaxVerbField(BaseModelWithLaxConfig):
    """Pydantic model for lax `verb` field.

    Lightest definition of a verb field compliant to the specification.
    """

    id: str


class PartialSuccessError(BaseModel):
    """One rejected statement in a partial-success POST batch."""

    index: int
    reason: str


class PartialSuccessResponse(BaseModel):
    """Response body when ``partialSuccess=true`` on POST /xAPI/statements."""

    inserted: int
    rejected: int
    ids: List[str] = Field(
        default_factory=list,
        description="IDs of statements stored by the LRS during this request",
    )
    errors: List[PartialSuccessError] = Field(default_factory=list)


class LaxStatement(BaseModelWithLaxConfig):
    """Pydantic model for lax statement.

    It accepts without validating all fields beyond the bare minimum required to
    qualify an object as an XAPI statement.
    """

    actor: Union[BaseXapiAgent, BaseXapiGroup]
    id: Optional[UUID] = None
    object: LaxObjectField
    verb: LaxVerbField
