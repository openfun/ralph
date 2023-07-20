"""`Scorm Profile` activity types definitions."""

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition


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
