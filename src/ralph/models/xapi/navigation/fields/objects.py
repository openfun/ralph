"""Navigation xAPI events object fields definitions"""

from typing import Literal, Optional

from ...base import BaseModelWithConfig
from ...constants import ACTIVITY_PAGE_DISPLAY, ACTIVITY_PAGE_ID, LANG_EN_US_DISPLAY
from ...fields.objects import ObjectDefinitionExtensionsField, ObjectField


class PageObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    WARNING: It doesn't include the recommended `description` field nor the optional `moreInfo`,
    `Interaction properties` and `extensions` fields.

    Attributes:
       type (str): Consists of the value `http://activitystrea.ms/schema/1.0/page`.
       name (dict): Consists of the dictionary `{"en-US": "page"}`.
       extensions (dict): See ObjectDefinitionExtensionsField.
    """

    name: dict[Literal[LANG_EN_US_DISPLAY], Literal[ACTIVITY_PAGE_DISPLAY]] = {
        LANG_EN_US_DISPLAY: ACTIVITY_PAGE_DISPLAY
    }
    type: Literal[ACTIVITY_PAGE_ID] = ACTIVITY_PAGE_ID
    extensions: Optional[ObjectDefinitionExtensionsField]


class PageObjectField(ObjectField):
    """Represents the `object` xAPI field for page viewed xAPI statement.

    WARNING: It doesn't include the optional `objectType` field.

    Attributes:
        definition (PageObjectDefinitionField): See PageObjectDefinitionField.
    """

    definition: PageObjectDefinitionField = PageObjectDefinitionField()
