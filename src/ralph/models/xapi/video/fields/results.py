"""Video xAPI events result fields definitions"""

from datetime import timedelta
from typing import Literal, Optional

from pydantic import Field, NonNegativeFloat

from ...base import BaseModelWithConfig
from ...fields.results import ResultField
from ..constants import (
    VIDEO_EXTENSION_CC_ENABLED,
    VIDEO_EXTENSION_PLAYED_SEGMENTS,
    VIDEO_EXTENSION_PROGRESS,
    VIDEO_EXTENSION_TIME,
    VIDEO_EXTENSION_TIME_FROM,
    VIDEO_EXTENSION_TIME_TO,
)


class VideoResultExtensionsField(BaseModelWithConfig):
    """Represents the result.extensions field for video `played` xAPI statement.

    Attributes:
        playedSegments (str): Consists of parts of the video the actor watched during
            current registration in chronological order (for example,
            "0[.]5[,]12[.]22[,]15[.]55[,]55[.]99.33[,]99.33").
        time (float): Consists of the video time code when the event was emitted.
    """

    time: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_TIME)
    playedSegments: Optional[str] = Field(alias=VIDEO_EXTENSION_PLAYED_SEGMENTS)


class VideoPausedResultExtensionsField(VideoResultExtensionsField):
    """Represents the result.extensions field for video `paused` xAPI statement.

    Attributes:
        progress (float): Consists of the ratio of media consumed by the actor.
    """

    progress: Optional[NonNegativeFloat] = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoSeekedResultExtensionsField(BaseModelWithConfig):
    """Represents the result.extensions field for video `seeked` xAPI statement.

    Attributes:
        timeFrom (float): Consists of the point in time the actor changed from in a
            media object during a seek operation.
        timeTo (float): Consists of the point in time the actor changed to in a media
            object during a seek operation.
    """

    timeFrom: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_TIME_FROM)
    timeTo: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_TIME_TO)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoCompletedResultExtensionsField(VideoResultExtensionsField):
    """Represents the result.extensions field for video `completed` xAPI statement.

    Attributes:
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    progress: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoTerminatedResultExtensionsField(VideoResultExtensionsField):
    """Represents the result.extensions field for video `terminated` xAPI statement.

    Attributes:
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    progress: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoEnableClosedCaptioningResultExtensionsField(VideoResultExtensionsField):
    """Represents the result.extensions field for video enable closed captioning
    `interacted` xAPI statement.

    Attributes:
        ccEnabled (bool): Indicates whether subtitles are enabled.
    """

    ccEnabled: bool = Field(alias=VIDEO_EXTENSION_CC_ENABLED)

    class Config:  # pylint: disable=missing-class-docstring
        min_anystr_length = 0


class VideoPlayedResultField(ResultField):
    """Represents the result field for video `played` xAPI statement.

    Attributes:
        extensions (dict): See VideoResultExtensionsField.
    """

    extensions: VideoResultExtensionsField


class VideoPausedResultField(ResultField):
    """Represents the result field for video `paused` xAPI statement.

    Attributes:
        extensions (dict): See VideoPausedResultExtensionsField.
    """

    extensions: VideoPausedResultExtensionsField


class VideoSeekedResultField(ResultField):
    """Represents the result field for video `seeked` xAPI statement.

    Attributes:
        extensions (dict): See VideoSeekedResultExtensionsField.
    """

    extensions: VideoSeekedResultExtensionsField


class VideoCompletedResultField(ResultField):
    """Represents the result field for video `completed` xAPI statement.

    Attributes:
        extensions (dict): See VideoCompletedResultExtensionsField.
        completion (bool): Consists of the value `True`.
        duration (str): Consists of the total time spent consuming the video under
            current registration.
    """

    extensions: VideoCompletedResultExtensionsField
    completion: Optional[Literal[True]]
    duration: Optional[timedelta]


class VideoTerminatedResultField(ResultField):
    """Represents the result field for video `terminated` xAPI statement.

    Attributes:
        extensions (dict): See VideoTerminatedResultExtensionsField.
    """

    extensions: VideoTerminatedResultExtensionsField


class VideoEnableClosedCaptioningResultField(ResultField):
    """Represents the result field for video enable closed captioning
    `interacted` xAPI statement.

    Attributes:
        extensions (dict): See VideoEnableClosedCaptioningResultExtensionsField.
    """

    extensions: VideoEnableClosedCaptioningResultExtensionsField


class VideoVolumeChangeInteractionResultField(ResultField):
    """Represents the result field for video volume change
    `interacted` xAPI statement.

    Attributes:
        extensions (dict): See VideoResultExtensionsField.
    """

    extensions: VideoResultExtensionsField


class VideoScreenChangeInteractionResultField(ResultField):
    """Represents the result field for video screen change `interacted` xAPI statement.

    Attributes:
        extensions (dict): See VideoResultExtensionsField.
    """

    extensions: VideoResultExtensionsField
