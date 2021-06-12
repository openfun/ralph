"""Problem interaction xAPI object field definitions"""

from typing import Literal, Optional

from pydantic import Field

from ralph.models.xapi.config import BaseModelWithConfig
from ralph.models.xapi.constants import (
    ACTIVITY_INTERACTION_DISPLAY,
    ACTIVITY_INTERACTION_ID,
    LANG_EN_US_DISPLAY,
)
from ralph.models.xapi.fields.objects import (
    ObjectDefinitionExtensionsField,
    ObjectField,
)
from ralph.models.xapi.problem.constants import (
    EXTENSION_SUPPLEMENTAL_INFO_ID,
    EXTENSION_TOTAL_ITEMS_ID,
)


class InteractionObjectDefinitionExtensionsField(ObjectDefinitionExtensionsField):
    """Represents the `object.definition.extensions` xAPI field.

    Attributes:
        supplemental_info (int): Consists of the the index of the hint the user received.
        total_items (int): Consists of the total number of available hints.
    """

    supplemental_info: Optional[int] = Field(alias=EXTENSION_SUPPLEMENTAL_INFO_ID)
    total_items: Optional[int] = Field(alias=EXTENSION_TOTAL_ITEMS_ID)


class InteractionObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field of an interaction.

    WARNING: It doesn't include the recommended `description` field nor the optional `moreInfo`
    and `Interaction properties` fields.

    Attributes:
       name (dict): Consists of the dictionary `{"en-US": "interaction"}`.
       type (str): Consists of the value `http://adlnet.gov/expapi/activities/interaction`.
       extensions (dict): See ObjectDefinitionExtensionsField.
    """

    name: dict[Literal[LANG_EN_US_DISPLAY], Literal[ACTIVITY_INTERACTION_DISPLAY]] = {
        LANG_EN_US_DISPLAY: ACTIVITY_INTERACTION_DISPLAY
    }
    type: Literal[ACTIVITY_INTERACTION_ID] = ACTIVITY_INTERACTION_ID
    extensions: Optional[InteractionObjectDefinitionExtensionsField]


class InteractionObjectField(ObjectField):
    """Represents the `object` xAPI field of an interaction.

    WARNING: It doesn't include the optional `objectType` field.

    Attributes:
        definition (InteractionObjectDefinitionField): See InteractionObjectDefinitionField.
    """

    definition: InteractionObjectDefinitionField = InteractionObjectDefinitionField()
