"""Base xAPI model definition"""

from datetime import datetime
from uuid import UUID

from .config import BaseModelWithConfig
from .fields.actors import ActorField


class BaseXapiModel(BaseModelWithConfig):
    """Base model for xAPI statements.

    WARNING: It doesn't include the required `verb` and `object` fields nor the optional
    `context`, `result`, `stored`, `authority`, `version` and `attachments` fields.

    Attributes:
        id (UUID): Consists of a generated UUID string from the source event string.
        actor (ActorField): See ActorField.
        timestamp (datetime): Consists of the UTC time in ISO format when the event was emitted.
    """

    id: UUID
    actor: ActorField
    timestamp: datetime
