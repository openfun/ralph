"""Navigation xAPI events object fields definitions"""

from typing import Optional

from ...constants import ACTIVITY_PAGE_DISPLAY, ACTIVITY_PAGE_ID, LANG_EN_US_DISPLAY
from ...fields.objects import ObjectDefinitionExtensionsField
from ...fields.unnested_objects import ActivityObjectField, ObjectDefinitionField


class PageObjectDefinitionField(ObjectDefinitionField):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    Attributes:
       type (str): Consists of the value `http://activitystrea.ms/schema/1.0/page`.
       name (dict): Consists of the dictionary `{"en-US": "page"}`.
       extensions (dict): See ObjectDefinitionExtensionsField.
    """

    name: dict[LANG_EN_US_DISPLAY, ACTIVITY_PAGE_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: ACTIVITY_PAGE_DISPLAY.__args__[0]
    }
    type: ACTIVITY_PAGE_ID = ACTIVITY_PAGE_ID.__args__[0]
    extensions: Optional[ObjectDefinitionExtensionsField]


class PageObjectField(ActivityObjectField):
    """Represents the `object` xAPI field for page viewed xAPI statement.

    Attributes:
        definition (dict): See PageObjectDefinitionField.
    """

    definition: PageObjectDefinitionField = PageObjectDefinitionField()
