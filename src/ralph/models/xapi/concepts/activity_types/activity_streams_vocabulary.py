"""`Activity streams vocabulary` activity types definitions."""

import sys

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


# Page


class PageActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for page `Activity` type `definition` property.

    Attributes:
       type (str): Consists of the value `http://activitystrea.ms/schema/1.0/page`.
    """

    type: Literal["http://activitystrea.ms/schema/1.0/page"] = (
        "http://activitystrea.ms/schema/1.0/page"
    )


class PageActivity(BaseXapiActivity):
    """Pydantic model for page `Activity` type.

    Attributes:
        definition (dict): See PageActivityDefinition.
    """

    definition: PageActivityDefinition = PageActivityDefinition()


# File


class FileActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for file `Activity` type `definition` property.

    Attributes:
       type (str): Consists of the value `http://activitystrea.ms/file`.
    """

    type: Literal["http://activitystrea.ms/file"] = "http://activitystrea.ms/file"


class FileActivity(BaseXapiActivity):
    """Pydantic model for file `Activity` type.

    Attributes:
        definition (dict): See FileActivityDefinition.
    """

    definition: FileActivityDefinition
