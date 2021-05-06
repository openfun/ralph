"""Common xAPI object field definitions"""

from pydantic import AnyUrl

from ..config import BaseModelWithConfig
from ..constants import EN, PAGE, XAPI_ACTIVITY_PAGE


class PageObjectDefinitionField(BaseModelWithConfig):
    """Represents the `object.definition` xAPI field for page viewed xAPI statement.

    WARNING: It don't include the recommended `description` field nor the optional `moreInfo`,
    `Interaction properties` and `extensions` fields.

    Attributes:
       type (str): Consists of the value `http://activitystrea.ms/schema/1.0/page`
       name (dict): Consists of the dictionary `{"en": "page"}`
    """

    type: XAPI_ACTIVITY_PAGE = XAPI_ACTIVITY_PAGE.__args__[0]
    name: dict[EN, PAGE] = {EN.__args__[0]: PAGE.__args__[0]}


class PageObjectField(BaseModelWithConfig):
    """Represents the `object` xAPI field for page viewed xAPI statement.

    WARNING: It don't include the optional `objectType` field.

    Attributes:
        id (URL): Consists of an identifier for a single unique Activity.
        definition (PageObjectDefinitionField): see PageObjectDefinitionField.
    """

    id: AnyUrl
    definition: PageObjectDefinitionField = PageObjectDefinitionField()
