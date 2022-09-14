"""Define API-specific data models so we can be exactly as lax as we want
when it comes to exact object shape and validation.
"""
from typing import Optional
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Extra

from ..models.xapi.fields.actors import ActorField


class ErrorDetail(BaseModel):
    """
    Type for return value for errors raised in API endpoints.
    Useful for OpenAPI documentation generation.
    """

    detail: str


class BaseModelWithLaxConfig(BaseModel):
    """Common base lax model to perform light input validation as
    we receive statements through the API.
    """

    class Config:
        """Enable extra properties so we do not have to perform comprehensive
        validation.
        """

        extra = Extra.allow


class LaxObjectField(BaseModelWithLaxConfig):
    """Lightest definition of an object field compliant to the specification."""

    id: AnyUrl


class LaxVerbField(BaseModelWithLaxConfig):
    """Lightest definition of a verb field compliant to the specification."""

    id: AnyUrl


class LaxStatement(BaseModelWithLaxConfig):
    """
    Lax definition of an XAPI statement that accepts without validating them all
    fields beyond the bare minimum required to qualify an object as an XAPI statement.
    """

    actor: ActorField
    id: Optional[UUID]
    object: LaxObjectField
    verb: LaxVerbField
