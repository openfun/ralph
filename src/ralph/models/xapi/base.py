"""Base xAPI model definition"""

from datetime import datetime

from pydantic import UUID4

from .config import BaseModelWithConfig
from .fields.actors import ActorField


class BaseXapiModel(BaseModelWithConfig):
    """Base model for xAPI statements.

    WARNING: It doesn't include the required `verb` and `object` fields nor the optional
    `context`, `result`, `stored`, `authority`, `version` and `attachments` fields.

    Attributes:
        id (UUID4): Consists of a generated UUID4 from the source event string.
        actor (ActorField): See ActorField.
        timestamp (datetime): Consists of the UTC time in ISO format when the event was emitted.
    """

    id: UUID4
    actor: ActorField
    timestamp: datetime
