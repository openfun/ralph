"""Base xAPI model configuration."""

from pydantic import BaseModel, Extra


class BaseModelWithConfig(BaseModel):
    """Pydantic model for base configuration shared among all models."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.forbid
        min_anystr_length = 1


class BaseExtensionModelWithConfig(BaseModel):
    """Pydantic model for extension configuration shared among all models."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.allow
        min_anystr_length = 0
