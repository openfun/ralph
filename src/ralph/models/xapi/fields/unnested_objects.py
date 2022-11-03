"""Common xAPI object field definitions."""

from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import AnyUrl, StrictStr, constr, validator

from ..config import BaseModelWithConfig
from .common import IRI, LanguageMap


class ObjectDefinitionField(BaseModelWithConfig):
    """Pydantic model for `object.definition` field.

    Attributes:
        name (LanguageMap): Consists of the human readable/visual name of the Activity.
        description (LanguageMap): Consists of a description of the Activity.
        type (IRI): Consists of the type of the Activity.
        moreInfo (URL): Consists of an URL to a document about the Activity.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    name: Optional[LanguageMap]
    description: Optional[LanguageMap]
    type: Optional[IRI]
    moreInfo: Optional[AnyUrl]
    extensions: Optional[dict[IRI, Union[str, int, bool, list, dict, None]]]


class InteractionComponent(BaseModelWithConfig):
    """Pydantic model for an interaction component.

    Attributes:
        id (str): Consists of an identifier of the interaction component.
        description (LanguageMap): Consists of the description of the interaction.
    """

    id: constr(regex=r"^[^\s]+$")  # noqa:F722
    description: Optional[LanguageMap]


class InteractionObjectDefinitionField(ObjectDefinitionField):
    """Pydantic model for `object.definition` field.

    It is defined for field with interaction properties.

    Attributes:
        interactionType (str): Consists of the type of the interaction.
        correctResponsesPattern (list): Consists of a pattern for the correct response.
        choices (list): Consists of a list of selectable choices.
        scale (list): Consists of a list of the options on the `likert` scale.
        source (list): Consists of a list of sources to be matched.
        target (list): Consists of a list of targets to be matched.
        steps (list): Consists of a list of the elements making up the interaction.
    """

    interactionType: Literal[
        "true-false",
        "choice",
        "fill-in",
        "long-fill-in",
        "matching",
        "performance",
        "sequencing",
        "likert",
        "numeric",
        "other",
    ]
    correctResponsesPattern: Optional[list[StrictStr]]
    choices: Optional[list[InteractionComponent]]
    scale: Optional[list[InteractionComponent]]
    source: Optional[list[InteractionComponent]]
    target: Optional[list[InteractionComponent]]
    steps: Optional[list[InteractionComponent]]

    @validator("choices", "scale", "source", "target", "steps")
    @classmethod
    def check_unique_ids(cls, value):
        """Checks the uniqueness of interaction components IDs."""

        if len(value) != len({x.id for x in value}):
            raise ValueError("Duplicate InteractionComponents are not valid")


class ActivityObjectField(BaseModelWithConfig):
    """Pydantic model for `object` field.

    It is defined for Activity type.

    Attributes:
        objectType (str): Consists of the value `Activity`.
        id (IRI): Consists of an identifier for a single unique Activity.
        definition (dict): See ObjectDefinitionField.
    """

    id: IRI
    objectType: Optional[Literal["Activity"]]
    definition: Optional[Union[ObjectDefinitionField, InteractionObjectDefinitionField]]


class StatementRefObjectField(BaseModelWithConfig):
    """Pydantic model for `object` field.

    It is defined for StatementRef type.

    Attributes:
        objectType (str): Consists of the value `StatementRef`.
        id (UUID): Consists of the UUID of the referenced statement.
    """

    id: UUID
    objectType: Literal["StatementRef"]


UnnestedObjectField = Union[ActivityObjectField, StatementRefObjectField]
