"""Base xAPI `Object` definitions (2)."""

# Nota bene: we split object definitions into `objects.py` and `unnested_objects.py`
# because of the circular dependency : objects -> context -> objects.

from datetime import datetime
from typing import List, Optional, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .attachments import BaseXapiAttachment
from .contexts import BaseXapiContext
from .groups import BaseXapiGroup
from .results import BaseXapiResult
from .unnested_objects import BaseXapiUnnestedObject
from .verbs import BaseXapiVerb


class BaseXapiSubStatement(BaseModelWithConfig):
    """Pydantic model for `SubStatement` type property.

    Attributes:
        actor (dict): See BaseXapiAgent and BaseXapiGroup.
        verb (dict): See BaseXapiVerb.
        object (dict): See BaseXapiUnnestedObject.
        objecType (dict): Consists of the value `SubStatement`.
    """

    actor: Union[BaseXapiAgent, BaseXapiGroup]
    verb: BaseXapiVerb
    object: BaseXapiUnnestedObject
    objectType: Literal["SubStatement"]
    result: Optional[BaseXapiResult] = None
    context: Optional[BaseXapiContext] = None
    timestamp: Optional[datetime] = None
    attachments: Optional[List[BaseXapiAttachment]] = None


BaseXapiObject = Union[
    BaseXapiUnnestedObject,
    BaseXapiSubStatement,
    BaseXapiAgent,
    BaseXapiGroup,
]
