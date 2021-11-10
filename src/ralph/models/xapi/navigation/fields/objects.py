"""Navigation xAPI events object fields definitions"""

from typing import Optional

from ...base import BaseModelWithConfig
from ...constants import ACTIVITY_PAGE_DISPLAY, ACTIVITY_PAGE_ID, LANG_EN_DISPLAY
from ...fields.objects import ObjectDefinitionExtensionsField, ObjectField


class PageObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    WARNING: It doesn't include the recommended `description` field nor the optional
        `moreInfo`, `Interaction properties` and `extensions` fields.

    Attributes:
       type (str): Consists of the value `http://activitystrea.ms/schema/1.0/page`.
       name (dict): Consists of the dictionary `{"en": "page"}`.
       extensions (dict): See ObjectDefinitionExtensionsField.
    """

    name: dict[LANG_EN_DISPLAY, ACTIVITY_PAGE_DISPLAY] = {
        LANG_EN_DISPLAY.__args__[0]: ACTIVITY_PAGE_DISPLAY.__args__[0]
    }
    type: ACTIVITY_PAGE_ID = ACTIVITY_PAGE_ID.__args__[0]
    extensions: Optional[ObjectDefinitionExtensionsField]


class PageObjectField(ObjectField):
    """Represents the `object` xAPI field for page viewed xAPI statement.

    WARNING: It doesn't include the optional `objectType` field.

    Attributes:
        definition (PageObjectDefinitionField): See PageObjectDefinitionField.
    """

    definition: PageObjectDefinitionField = PageObjectDefinitionField()
