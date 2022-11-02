"""Base xAPI model configuration"""

from pydantic import BaseModel, Extra


class BaseModelWithConfig(BaseModel):
    """Base model defining configuration shared among all models."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.forbid
        min_anystr_length = 1
