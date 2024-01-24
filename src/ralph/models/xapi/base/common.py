"""Common for xAPI base definitions."""

from typing import Dict, Type, Union

from langcodes import tag_is_valid
from pydantic import RootModel, model_validator, validate_email
from rfc3987 import parse

from ralph.conf import NonEmptyStrictStr


class IRI(RootModel[Union["IRI", str]]):
    """Pydantic custom data type validating RFC 3987 IRIs."""

    def __hash__(self):  # noqa: D105
        return hash(str(self.root))

    def __str__(self):  # noqa: D105
        return str(self.root)

    @model_validator(mode="before")
    @classmethod
    def validate_iri(cls, iri):
        """Check whether the provided IRI is a valid RFC 3987 IRI."""
        parse(str(iri), rule="IRI")
        return str(iri)


class LanguageTag(RootModel[Union[str, "LanguageTag"]]):
    """Pydantic custom data type validating RFC 5646 Language tags."""

    def __hash__(self):  # noqa: D105
        return hash(str(self.root))

    def __str__(self):  # noqa: D105
        return str(self.root)

    @model_validator(mode="before")
    @classmethod
    def validate_language_tag(cls, tag):
        """Check whether the provided tag is a valid RFC 5646 Language tag."""
        if not tag_is_valid(str(tag)):
            raise TypeError("Invalid RFC 5646 Language tag")
        return str(tag)


LanguageMap = Dict[LanguageTag, NonEmptyStrictStr]


class MailtoEmail(RootModel[str]):
    """Pydantic custom data type validating `mailto:email` format."""

    @model_validator(mode="after")
    def validate(self) -> Type["MailtoEmail"]:
        """Check whether the provided value follows the `mailto:email` format."""
        if not self.root.startswith("mailto:"):
            raise TypeError("Invalid `mailto:email` value")
        valid = validate_email(self.root[7:])
        self.root = f"mailto:{valid[1]}"
        return self
