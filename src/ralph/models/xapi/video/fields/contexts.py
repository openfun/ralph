"""Video xAPI events context fields definitions"""

from typing import List, Literal, Optional

from pydantic import UUID5, Field

from ...base import BaseModelWithConfig
from ..constants import VIDEO_CONTEXT_CATEGORY, VIDEO_EXTENSION_SESSION_ID


class VideoPlayedContextExtensionsField(BaseModelWithConfig):
    """Represents the context.extensions field for video `played` xAPI statement.

    Attributes:
        session(uuid5): Consists of the ID of the active session.
    """

    session: Optional[UUID5] = Field(alias=VIDEO_EXTENSION_SESSION_ID)


class VideoPlayedContextActivitiesField(BaseModelWithConfig):
    """Represents the contextActivities field for video `played` xAPI statement.

    Attributes:
        category(dict): Consists of the dictionary {"id": "https://w3id.org/xapi/video"}.
    """

    category: List[dict[Literal["id"], VIDEO_CONTEXT_CATEGORY]] = [
        {Literal["id"]: VIDEO_CONTEXT_CATEGORY.__args__[0]}
    ]


class VideoPlayedContextField(BaseModelWithConfig):
    """Represents the context field for video `played` xAPI statement.

    Attributes:
        extensions(VideoPlayedContextExtensionsField): See VideoPlayedContextExtensionsField.
        contextActivities (see VideoPlayedContextActivitiesField): See
            VideoPlayedContextActivitiesField.
    """

    extensions: Optional[VideoPlayedContextExtensionsField]
    contextActivities: Optional[VideoPlayedContextActivitiesField]
