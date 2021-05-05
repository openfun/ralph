"""Base xAPI model configuration"""

from pydantic import BaseModel


class BaseModelWithConfig(BaseModel):
    """Base model defining configuration shared among all models."""

    class Config:  # pylint: disable=missing-class-docstring
        extra = "forbid"
        min_anystr_length = 1
