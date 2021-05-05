"""Common xAPI object field definitions"""

from typing import Optional

from pydantic import AnyUrl, Field

from ..config import BaseModelWithConfig
from ..constants import (
    ACTIVITY_PAGE_DISPLAY,
    ACTIVITY_PAGE_ID,
    EXTENSION_COURSE_ID,
    EXTENSION_MODULE_ID,
    EXTENSION_SCHOOL_ID,
    LANG_EN_DISPLAY,
)


class ObjectField(BaseModelWithConfig):
    """Represents the `object` xAPI field.

    WARNING: It doesn't include the optional `objectType` and `definition` fields.

    Attributes:
        id (URL): Consists of an identifier for a single unique Activity.
    """

    id: AnyUrl


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


class PageObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    WARNING: It doesn't include the recommended `description` field nor the optional `moreInfo`,
    `Interaction properties` and `extensions` fields.

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

    definition: PageObjectDefinitionField
