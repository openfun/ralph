"""`Scorm Profile` activity types definitions."""

import sys

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


# Document


class DocumentActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for document `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://id.tincanapi.com/activitytype/document`.
    """

    type: Literal["http://id.tincanapi.com/activitytype/document"]


class DocumentActivity(BaseXapiActivity):
    """Pydantic model for document `Activity` type.

    Attributes:
        definition (dict): see DocumentActivityDefinition.
    """

    definition: DocumentActivityDefinition
