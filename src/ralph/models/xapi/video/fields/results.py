"""Video xAPI events result fields definitions."""

from datetime import timedelta
from typing import Literal, Optional

from pydantic import Field

from ...base import BaseModelWithConfig
from ...fields.results import ResultField
from ..constants import (
    VIDEO_EXTENSION_LENGTH,
    VIDEO_EXTENSION_PLAYED_SEGMENTS,
    VIDEO_EXTENSION_PROGRESS,
    VIDEO_EXTENSION_TIME,
    VIDEO_EXTENSION_TIME_FROM,
    VIDEO_EXTENSION_TIME_TO,
)


class VideoActionResultExtensionsField(BaseModelWithConfig):
    """Represents the result.extensions field for video `played` xAPI statement.

    Attributes:
        time (float): Consists of the video time code when the event was emitted.
    """

    time: Optional[float] = Field(alias=VIDEO_EXTENSION_TIME)


class VideoPausedResultExtensionsField(VideoActionResultExtensionsField):
    """Represents the result.extensions field for video `played` xAPI statement.

    Attributes:
        playedSegments (str): Consists of parts of the video the actor watched during
            current registration in chronological order (for example,
            "0[.]5[,]12[.]22[,]15[.]55[,]55[.]99.33[,]99.33").
        progress (float): Consists of the ratio of media consumed by the actor.
    """

    playedSegments: Optional[str] = Field(alias=VIDEO_EXTENSION_PLAYED_SEGMENTS)
    progress: Optional[float] = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoSeekedResultExtensionsField(BaseModelWithConfig):
    """Represents the result.extensions field for video `seeked` xAPI statement.

    Attributes:
        timeFrom (float): Consists of the point in time the actor changed from in a
            media object during a seek operation.
        timeTo (float): Consists of the point in time the actor changed to in a media
            object during a seek operation.
        length (float): Consists of the actual length of the media in seconds.
        playedSegments (str): Consists of parts of the video the actor watched during
            current registration in chronological order.
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    timeFrom: Optional[float] = Field(alias=VIDEO_EXTENSION_TIME_FROM)
    timeTo: Optional[float] = Field(alias=VIDEO_EXTENSION_TIME_TO)
    length: Optional[float] = Field(alias=VIDEO_EXTENSION_LENGTH)
    playedSegments: Optional[str] = Field(alias=VIDEO_EXTENSION_PLAYED_SEGMENTS)
    progress: Optional[float] = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoCompletedResultExtensionsField(VideoActionResultExtensionsField):
    """Represents the result.extensions field for video `completed` xAPI statement.

    Attributes:
        playedSegments (str): Consists of parts of the video the actor watched during
            current registration in chronological order.
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    playedSegments: Optional[str] = Field(alias=VIDEO_EXTENSION_PLAYED_SEGMENTS)
    progress: Optional[float] = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoTerminatedResultExtensionsField(VideoActionResultExtensionsField):
    """Represents the result.extensions field for video `terminated` xAPI statement.

    Attributes:
        playedSegments (str): Consists of parts of the video the actor watched during
            current registration in chronological order.
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    playedSegments: Optional[str] = Field(alias=VIDEO_EXTENSION_PLAYED_SEGMENTS)
    progress: Optional[float] = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoPlayedResultField(ResultField):
    """Represents the result field for video `played` xAPI statement.

    Attributes:
        extensions (dict): See VideoActionResultExtensionsField.
    """

    extensions: Optional[VideoActionResultExtensionsField]


class VideoPausedResultField(ResultField):
    """Represents the result field for video `paused` xAPI statement.

    Attributes:
        extensions (dict): See VideoPausedResultExtensionsField.
    """

    extensions: Optional[VideoPausedResultExtensionsField]


class VideoSeekedResultField(ResultField):
    """Represents the result field for video `seeked` xAPI statement.

    Attributes:
        extensions (dict): See VideoSeekedResultExtensionsField.
    """

    extensions: Optional[VideoSeekedResultExtensionsField]


class VideoCompletedResultField(ResultField):
    """Represents the result field for video `completed` xAPI statement.

    Attributes:
        extensions (dict): See VideoCompletedResultExtensionsField.
        completion (bool): Consists of the value `True`.
        duration (str): Consists of the total time spent consuming the video under
            current registration.
    """

    extensions: Optional[VideoCompletedResultExtensionsField]
    completion: Optional[Literal[True]]
    duration: Optional[timedelta]


class VideoTerminatedResultField(ResultField):
    """Represents the result field for video `terminated` xAPI statement.

    Attributes:
        extensions (dict): See VideoTerminatedResultExtensionsField.
    """

    extensions: Optional[VideoTerminatedResultExtensionsField]


class VideoInteractedResultField(ResultField):
    """Represents the result field for video `terminated` xAPI statement.

    Attributes:
        extensions (dict): See VideoActionResultExtensionsField.
    """

    extensions: Optional[VideoActionResultExtensionsField]
