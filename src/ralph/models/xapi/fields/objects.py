"""Common xAPI object field definitions"""

from typing import Literal, Optional

from pydantic import AnyUrl, Field

from ..config import BaseModelWithConfig
from ..constants import (
    EXTENSION_COURSE_ID,
    EXTENSION_MODULE_ID,
    EXTENSION_SCHOOL_ID,
    LANG_EN_US_DISPLAY,
)


class InteractionComponent(BaseModelWithConfig):
    """Represents an xAPI Interaction component.

    Attributes:
        id (str): Consists of an identifier of the interaction component.
        description (dict): Consists of the description of the interaction component.
    """

    id: str
    description: Optional[dict[Literal[LANG_EN_US_DISPLAY], str]]


class ObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field.

    Attributes:
        name (dict): Consists of the human readable/visual name of the Activity.
        description (dict): Consists of a description of the Activity.
        type (URL): Consists of the type of the Activity.
        moreInfo (URL): Consists of an URL to a document about the Activity.
        interactionType (str): Consists of the type of the interaction.
        correctResponsesPattern (list): Consists of a pattern for the correct response.
        choices (list): Consists of a list of selectable choices.
        scale (list): Consists of a list of the options on the `likert` scale.
        source (list): Consists of a list of sources to be matched.
        target (list): Consists of a list of targets to be matched.
        steps (list): Consists of a list of the elements making up the interaction.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    name: Optional[dict[LANG_EN_US_DISPLAY, str]]
    description: Optional[dict[LANG_EN_US_DISPLAY, str]]
    type: Optional[AnyUrl]
    moreInfo: Optional[AnyUrl]
    interactionType: Optional[
        Literal[
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
    ]
    correctResponsesPattern: Optional[list[str]]
    choices: Optional[list[InteractionComponent]]
    scale: Optional[list[InteractionComponent]]
    source: Optional[list[InteractionComponent]]
    target: Optional[list[InteractionComponent]]
    steps: Optional[list[InteractionComponent]]
    extensions: Optional[dict]


class ObjectField(BaseModelWithConfig):
    """Represents the `object` xAPI field.

    Attributes:
        id (URL): Consists of an identifier for a single unique Activity.
        objectType (str): Consists of the value `Activity`.
        definition (dict): See ObjectDefinitionField.
    """

    id: AnyUrl
    objectType: Optional[Literal["Activity"]]
    definition: Optional[ObjectDefinitionField]


class ObjectDefinitionExtensionsField(BaseModelWithConfig):
    """Represents the `object.definition.extensions` xAPI field.

    Attributes:
        school (str): Consists of the name of the school.
        course (str): Consists of the name of the course.
        module (str): Consists of the name of the module.
    """

    school: Optional[str] = Field(alias=EXTENSION_SCHOOL_ID)
    course: Optional[str] = Field(alias=EXTENSION_COURSE_ID)
    module: Optional[str] = Field(alias=EXTENSION_MODULE_ID)
