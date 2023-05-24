"""`Virtual classroom` activity types definitions."""

import sys

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


# Virtual classroom


class VirtualClassroomActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for virtual classroom `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom`.
    """

    type: Literal[
        "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"
    ] = "https://w3id.org/xapi/virtual-classroom/activity-types/virtual-classroom"


class VirtualClassroomActivity(BaseXapiActivity):
    """Pydantic model for virtual classroom `Activity` type.

    Attributes:
        definition (dict): See VirtualClassroomActivityDefinition.
    """

    definition: VirtualClassroomActivityDefinition = (
        VirtualClassroomActivityDefinition()
    )
