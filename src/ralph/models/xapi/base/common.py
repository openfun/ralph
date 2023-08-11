"""Common for xAPI base definitions."""

from typing import Annotated, Dict

from langcodes import tag_is_valid
from pydantic import  StrictStr, validate_email
from pydantic.functional_validators import AfterValidator, BeforeValidator
from rfc3987 import parse


# class IRI(str):
#     """Pydantic custom data type validating RFC 3987 IRIs."""

#     @classmethod
#     def __get_validators__(cls):  # noqa: D105
#         def validate(iri: str):
#             """Checks whether the provided IRI is a valid RFC 3987 IRI."""
#             parse(iri, rule="IRI")
#             return cls(iri)

#         yield validate

def validate_iri(iri):
    parse(iri, rule="IRI")
    return iri

IRI = Annotated[str, BeforeValidator(validate_iri)]


def validate_language_tag(tag: str):
    """Checks whether the provided tag is a valid RFC 5646 Language tag."""
    if not tag_is_valid(tag):
        raise TypeError("Invalid RFC 5646 Language tag")
    return tag

LanguageTag = Annotated[str, AfterValidator(validate_language_tag)]

LanguageMap = Dict[LanguageTag, StrictStr]


# class MailtoEmail(str):
#     """Pydantic custom data type validating `mailto:email` format."""

#     @classmethod
#     def validate(cls, mailto: str):
#         """Check whether the provided value follows the `mailto:email` format."""
#         if not mailto.startswith("mailto:"):
#             raise TypeError("Invalid `mailto:email` value")
#         valid = validate_email(mailto[7:])
#         return cls(f"mailto:{valid[1]}")

#     @classmethod
#     def __get_validators__(cls):  # noqa: D105
#         yield cls.validate

def validate_mailto_email(mailto: str):
    """Check whether the provided value follows the `mailto:email` format."""
    if not mailto.startswith("mailto:"):
        raise TypeError("Invalid `mailto:email` value")
    valid = validate_email(mailto[7:])
    return f"mailto:{valid[1]}"

MailtoEmail = Annotated[str, AfterValidator(validate_mailto_email)]