"""Common xAPI object field definitions"""

from typing import Optional

from pydantic import AnyUrl, Field

from ..config import BaseModelWithConfig
from ..constants import EXTENSION_COURSE_ID, EXTENSION_MODULE_ID, EXTENSION_SCHOOL_ID


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
