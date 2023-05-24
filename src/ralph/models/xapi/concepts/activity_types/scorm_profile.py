"""`Scorm Profile` activity types definitions."""

import sys

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


# CMI Interaction


class CMIInteractionActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for CMI Interaction `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://adlnet.gov/expapi/activities/cmi.interaction`.
    """

    type: Literal[
        "http://adlnet.gov/expapi/activities/cmi.interaction"
    ] = "http://adlnet.gov/expapi/activities/cmi.interaction"


class CMIInteractionActivity(BaseXapiActivity):
    """Pydantic model for CMI Interaction `Activity` type.

    Attributes:
        definition (dict): see CMIInteractionActivityDefinition.
    """

    definition: CMIInteractionActivityDefinition = CMIInteractionActivityDefinition()


# Profile


class ProfileActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for profile `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://adlnet.gov/expapi/activities/profile`.
    """

    type: Literal[
        "http://adlnet.gov/expapi/activities/profile"
    ] = "http://adlnet.gov/expapi/activities/profile"


class ProfileActivity(BaseXapiActivity):
    """Pydantic model for profile `Activity` type.

    Attributes:
        definition (dict): see ProfileActivityDefinition.
    """

    definition: ProfileActivityDefinition = ProfileActivityDefinition()


# Course


class CourseActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for course `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://adlnet.gov/expapi/activities/course`.
    """

    type: Literal[
        "http://adlnet.gov/expapi/activities/course"
    ] = "http://adlnet.gov/expapi/activities/course"


class CourseActivity(BaseXapiActivity):
    """Pydantic model for course `Activity` type.

    Attributes:
        definition (dict): see CourseActivityDefinition.
    """

    definition: CourseActivityDefinition = CourseActivityDefinition()


# Module


class ModuleActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for module `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://adlnet.gov/expapi/activities/module`.
    """

    type: Literal[
        "http://adlnet.gov/expapi/activities/module"
    ] = "http://adlnet.gov/expapi/activities/module"


class ModuleActivity(BaseXapiActivity):
    """Pydantic model for module `Activity` type.

    Attributes:
        definition (dict): see ModuleActivityDefinition.
    """

    definition: ModuleActivityDefinition = ModuleActivityDefinition()
