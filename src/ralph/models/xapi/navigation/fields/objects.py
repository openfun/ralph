"""Navigation xAPI events object fields definitions."""

from typing import Dict, Optional

from ...constants import ACTIVITY_PAGE_DISPLAY, ACTIVITY_PAGE_ID, LANG_EN_US_DISPLAY
from ...fields.objects import ObjectDefinitionExtensionsField
from ...fields.unnested_objects import ActivityObjectField, ObjectDefinitionField


class PageObjectDefinitionField(ObjectDefinitionField):
    """Pydantic model for page viewed `object`.`definition` field.

    Attributes:
       type (str): Consists of the value `http://activitystrea.ms/schema/1.0/page`.
       name (dict): Consists of the dictionary `{"en-US": "page"}`.
       extensions (dict): See ObjectDefinitionExtensionsField.
    """

    name: Dict[LANG_EN_US_DISPLAY, ACTIVITY_PAGE_DISPLAY] = {
        LANG_EN_US_DISPLAY.__args__[0]: ACTIVITY_PAGE_DISPLAY.__args__[0]
    }
    type: ACTIVITY_PAGE_ID = ACTIVITY_PAGE_ID.__args__[0]
    extensions: Optional[ObjectDefinitionExtensionsField]


class PageObjectField(ActivityObjectField):
    """Pydantic model for page viewed `object` field.

    Attributes:
        definition (dict): See PageObjectDefinitionField.
    """

    definition: PageObjectDefinitionField = PageObjectDefinitionField()
