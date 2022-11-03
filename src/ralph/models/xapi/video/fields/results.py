"""Video xAPI events result fields definitions."""

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
    """Pydantic model for video `result`.`extensions` field.

    Attributes:
        playedSegments (str): Consists of parts of the video the actor watched during
            current registration in chronological order (for example,
            "0[.]5[,]12[.]22[,]15[.]55[,]55[.]99.33[,]99.33").
        time (float): Consists of the video time code when the event was emitted.
    """

    time: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_TIME)
    playedSegments: Optional[str] = Field(alias=VIDEO_EXTENSION_PLAYED_SEGMENTS)


class VideoPausedResultExtensionsField(VideoResultExtensionsField):
    """Pydantic model for video paused `result`.`extensions` field.

    Attributes:
        progress (float): Consists of the ratio of media consumed by the actor.
    """

    progress: Optional[NonNegativeFloat] = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        min_anystr_length = 0


class VideoSeekedResultExtensionsField(BaseModelWithConfig):
    """Pydantic model for video seeked `result`.`extensions` field.

    Attributes:
        timeFrom (float): Consists of the point in time the actor changed from in a
            media object during a seek operation.
        timeTo (float): Consists of the point in time the actor changed to in a media
            object during a seek operation.
    """

    timeFrom: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_TIME_FROM)
    timeTo: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_TIME_TO)

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        min_anystr_length = 0


class VideoCompletedResultExtensionsField(VideoResultExtensionsField):
    """Pydantic model for video completed `result`.`extensions` field.

    Attributes:
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    progress: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        min_anystr_length = 0


class VideoTerminatedResultExtensionsField(VideoResultExtensionsField):
    """Pydantic model for video terminated `result`.`extensions` field.

    Attributes:
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    progress: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_PROGRESS)

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        min_anystr_length = 0


class VideoEnableClosedCaptioningResultExtensionsField(VideoResultExtensionsField):
    """Pydantic model for video enable closed captioning `result`.`extensions` field.

    Attributes:
        ccEnabled (bool): Indicates whether subtitles are enabled.
    """

    ccEnabled: bool = Field(alias=VIDEO_EXTENSION_CC_ENABLED)

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        min_anystr_length = 0


class VideoPlayedResultField(ResultField):
    """Pydantic model for video played `result` field.

    Attributes:
        extensions (dict): See VideoResultExtensionsField.
    """

    extensions: VideoResultExtensionsField


class VideoPausedResultField(ResultField):
    """Pydantic model for video paused `result` field.

    Attributes:
        extensions (dict): See VideoPausedResultExtensionsField.
    """

    extensions: VideoPausedResultExtensionsField


class VideoSeekedResultField(ResultField):
    """Pydantic model for video seeked `result` field.

    Attributes:
        extensions (dict): See VideoSeekedResultExtensionsField.
    """

    extensions: VideoSeekedResultExtensionsField


class VideoCompletedResultField(ResultField):
    """Pydantic model for video completed `result` field.

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
    """Pydantic model for video terminated `result` field.

    Attributes:
        extensions (dict): See VideoTerminatedResultExtensionsField.
    """

    extensions: VideoTerminatedResultExtensionsField


class VideoEnableClosedCaptioningResultField(ResultField):
    """Pydantic model for video enable closed captioning `result` field.

    Attributes:
        extensions (dict): See VideoEnableClosedCaptioningResultExtensionsField.
    """

    extensions: VideoEnableClosedCaptioningResultExtensionsField


class VideoVolumeChangeInteractionResultField(ResultField):
    """Pydantic model for video volume change interaction `result` field.

    Attributes:
        extensions (dict): See VideoResultExtensionsField.
    """

    extensions: VideoResultExtensionsField


class VideoScreenChangeInteractionResultField(ResultField):
    """Pydantic model for video screen change interaction `result` field.

    Attributes:
        extensions (dict): See VideoResultExtensionsField.
    """

    extensions: VideoResultExtensionsField
