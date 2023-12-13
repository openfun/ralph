"""Common for xAPI base definitions."""

from typing import Annotated, Dict, Generator, Type

from langcodes import tag_is_valid
from pydantic import Field
from rfc3987 import parse

from ralph.conf import NonEmptyStr, NonEmptyStrictStr, NonEmptyStrictStrPatch


class IRI(NonEmptyStrictStrPatch):
    """Pydantic custom data type validating RFC 3987 IRIs."""

    @classmethod
    def __get_validators__(cls) -> Generator:  # noqa: D105
        def validate(iri: str) -> Type["IRI"]:
            """Check whether the provided IRI is a valid RFC 3987 IRI."""
            parse(iri, rule="IRI")
            return cls(iri)

        yield validate


class LanguageTag(NonEmptyStr):
    """Pydantic custom data type validating RFC 5646 Language tags."""

    @classmethod
    def __get_validators__(cls) -> Generator:  # noqa: D105
        def validate(tag: str) -> Type["LanguageTag"]:
            """Check whether the provided tag is a valid RFC 5646 Language tag."""
            if not tag_is_valid(tag):
                raise TypeError("Invalid RFC 5646 Language tag")
            return cls(tag)

        yield validate


LanguageMap = Dict[LanguageTag, NonEmptyStrictStr]  # TODO: change   back to strictstr


email_pattern = r"(^mailto:[-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])"
MailtoEmail = Annotated[str, Field(regex=email_pattern)]
