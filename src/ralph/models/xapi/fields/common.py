"""Common xAPI field definitions."""

from langcodes import tag_is_valid
from pydantic import StrictStr, validate_email
from rfc3987 import parse


class IRI(str):
    """Pydantic custom data type validating RFC 3987 IRIs."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(iri: str):
            """Checks whether the provided IRI is a valid RFC 3987 IRI."""
            parse(iri, rule="IRI")
            return cls(iri)

        yield validate


class LanguageTag(str):
    """Pydantic custom data type validating RFC 5646 Language tags."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(tag: str):
            """Checks whether the provided tag is a valid RFC 5646 Language tag."""
            if not tag_is_valid(tag):
                raise TypeError("Invalid RFC 5646 Language tag")
            return cls(tag)

        yield validate


LanguageMap = dict[LanguageTag, StrictStr]


class MailtoEmail(str):
    """Pydantic custom data type validating `mailto:email` format."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(mailto: str):
            """Checks whether the provided value follows the `mailto:email` format."""
            if not mailto.startswith("mailto:"):
                raise TypeError("Invalid `mailto:email` value")
            valid = validate_email(mailto[7:])
            return cls(f"mailto:{valid[1]}")

        yield validate
