"""Video xAPI events result fields definitions"""

from typing import Optional

from pydantic import Field

from ...base import BaseModelWithConfig
from ..constants import VIDEO_EXTENSION_TIME


class VideoPlayedResultExtensionsField(BaseModelWithConfig):
    """Represents the result.extensions field for video `played` xAPI statement.

    Attributes:
        time (float): Consists of the spent time on the video when the event was emitted.
    """

    time: Optional[float] = Field(alias=VIDEO_EXTENSION_TIME)


class VideoPlayedResultField(BaseModelWithConfig):
    """Represents the result field for video `played` xAPI statement.

    Attributes:
        extensions(VideoPlayedResultExtensionsField): See VideoPlayedResultExtensionsField.
    """

    extensions: Optional[VideoPlayedResultExtensionsField]
