"""Common for xAPI base definitions."""

from typing import Dict, Generator, Type

from langcodes import tag_is_valid
from pydantic import StrictStr, validate_email
from rfc3987 import parse


class IRI(str):
    """Pydantic custom data type validating RFC 3987 IRIs."""

    @classmethod
    # TODO[pydantic]: We couldn't refactor `__get_validators__`, please create the `__get_pydantic_core_schema__` manually.
    # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    def __get_validators__(cls) -> Generator:  # noqa: D105
        def validate(iri: str) -> Type["IRI"]:
            """Check whether the provided IRI is a valid RFC 3987 IRI."""
            parse(iri, rule="IRI")
            return cls(iri)

        yield validate


class LanguageTag(str):
    """Pydantic custom data type validating RFC 5646 Language tags."""

    @classmethod
    # TODO[pydantic]: We couldn't refactor `__get_validators__`, please create the `__get_pydantic_core_schema__` manually.
    # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    def __get_validators__(cls) -> Generator:  # noqa: D105
        def validate(tag: str) -> Type["LanguageTag"]:
            """Check whether the provided tag is a valid RFC 5646 Language tag."""
            if not tag_is_valid(tag):
                raise TypeError("Invalid RFC 5646 Language tag")
            return cls(tag)

        yield validate


LanguageMap = Dict[LanguageTag, StrictStr]


class MailtoEmail(str):
    """Pydantic custom data type validating `mailto:email` format."""

    @classmethod
    # TODO[pydantic]: We couldn't refactor `__get_validators__`, please create the `__get_pydantic_core_schema__` manually.
    # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    def __get_validators__(cls) -> Generator:  # noqa: D105
        def validate(mailto: str) -> Type["MailtoEmail"]:
            """Check whether the provided value follows the `mailto:email` format."""
            if not mailto.startswith("mailto:"):
                raise TypeError("Invalid `mailto:email` value")
            valid = validate_email(mailto[7:])
            return cls(f"mailto:{valid[1]}")

        yield validate
