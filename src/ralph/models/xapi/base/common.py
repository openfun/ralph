"""Common for xAPI base definitions."""

from typing import Dict, Generator, Type

from langcodes import tag_is_valid
from pydantic import StrictStr, validate_email
from rfc3987 import parse

from ralph.conf import NonEmptyStr, NonEmptyStrictStr, NonEmptyStrictStrPatch

from typing import Annotated
from pydantic import Field
from pydantic import BaseModel, root_validator

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
                print("Provided tag is:", tag)
                raise TypeError("Invalid RFC 5646 Language tag")
            return cls(tag)

        yield validate


LanguageMap = Dict[LanguageTag, NonEmptyStrictStr] # TODO: change  back to strictstr


email_pattern = r"(^mailto:[-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])"
MailtoEmail = Annotated[str, Field(regex=email_pattern)]

# class MailtoEmail(str):
#     """Pydantic custom data type validating `mailto:email` format."""

#     @classmethod
#     def __get_validators__(cls) -> Generator:  # noqa: D105
#         def validate(mailto: str) -> Type["MailtoEmail"]:
#             """Check whether the provided value follows the `mailto:email` format."""
#             if not mailto.startswith("mailto:"):
#                 raise TypeError(f"Invalid `mailto:email` value: {str(mailto)}")
#             valid = validate_email(mailto[7:])
#             return cls(f"mailto:{valid[1]}")

#         yield validate
