"""Base xAPI `Verb` definitions."""

from typing import Optional

from ..config import BaseModelWithConfig
from .common import IRI, LanguageMap


class BaseXapiVerb(BaseModelWithConfig):
    """Pydantic model for `verb` property.

    Attributes:
        id (IRI): Consists of an identifier for the verb.
        display (LanguageMap): Consists of a human readable representation of the verb.
    """

    id: IRI
    display: Optional[LanguageMap]
