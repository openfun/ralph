"""Common xAPI object field definitions."""

# Nota bene: we split object definitions into `objects.py` and `unnested_objects.py`
# because of the circular dependency : objects -> context -> objects.

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import Field

from ..config import BaseExtensionModelWithConfig, BaseModelWithConfig
from ..constants import EXTENSION_COURSE_ID, EXTENSION_MODULE_ID, EXTENSION_SCHOOL_ID
from .actors import ActorField
from .attachments import AttachmentField
from .contexts import ContextField
from .results import ResultField
from .unnested_objects import UnnestedObjectField
from .verbs import VerbField


class SubStatementObjectField(BaseModelWithConfig):
    """Pydantic model for `object` field.

    It is defined for SubStatement tyoe.

    Attributes:
        actor (ActorField): See ActorField.
        verb (VerbField): See VerbField.
        object (UnnestedObjectField): See UnnestedObjectField.
    """

    actor: ActorField
    verb: VerbField
    object: UnnestedObjectField
    objectType: Literal["SubStatement"]
    result: Optional[ResultField]
    context: Optional[ContextField]
    timestamp: Optional[datetime]
    attachments: Optional[list[AttachmentField]]


ObjectField = Union[UnnestedObjectField, SubStatementObjectField]


class ObjectDefinitionExtensionsField(BaseExtensionModelWithConfig):
    """Pydantic model for `object.definition.extensions` field.

    Attributes:
        school (str): Consists of the name of the school.
        course (str): Consists of the name of the course.
        module (str): Consists of the name of the module.
    """

    school: Optional[str] = Field(alias=EXTENSION_SCHOOL_ID)
    course: Optional[str] = Field(alias=EXTENSION_COURSE_ID)
    module: Optional[str] = Field(alias=EXTENSION_MODULE_ID)
