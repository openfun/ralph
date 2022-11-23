"""API-specific data models definition.

Allows to be exactly as lax as we want when it comes to exact object shape and
validation.
"""
from typing import Optional
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Extra

from ..models.xapi.fields.actors import ActorField


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

    class Config:
        """Enable extra properties.

        Useful for not having to perform comprehensive validation.
        """

        extra = Extra.allow


class LaxObjectField(BaseModelWithLaxConfig):
    """Pydantic model for lax `object` field.

    Lightest definition of an object field compliant to the specification.
    """

    id: AnyUrl


class LaxVerbField(BaseModelWithLaxConfig):
    """Pydantic model for lax `verb` field.

    Lightest definition of a verb field compliant to the specification.
    """

    id: AnyUrl


class LaxStatement(BaseModelWithLaxConfig):
    """Pydantic model for lax statement.

    It accepts without validating all fields beyond the bare minimum required to
    qualify an object as an XAPI statement.
    """

    actor: ActorField
    id: Optional[UUID]
    object: LaxObjectField
    verb: LaxVerbField
