"""Video xAPI events result fields definitions."""

from datetime import timedelta
from typing import Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from pydantic import Field, NonNegativeFloat

from ..base.results import BaseXapiResult
from ..concepts.constants.video import (
    CONTEXT_EXTENSION_CC_ENABLED,
    CONTEXT_EXTENSION_PLAYED_SEGMENTS,
    RESULT_EXTENSION_PROGRESS,
    RESULT_EXTENSION_TIME,
    RESULT_EXTENSION_TIME_FROM,
    RESULT_EXTENSION_TIME_TO,
)
from ..config import BaseExtensionModelWithConfig


class VideoResultExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for video `result`.`extensions` property.

    Attributes:
        playedSegments (str): Consists of parts of the video the actor watched during
            current registration in chronological order (for example,
            "0[.]5[,]12[.]22[,]15[.]55[,]55[.]99.33[,]99.33").
        time (float): Consists of the video time code when the event was emitted.
    """

    time: NonNegativeFloat = Field(alias=RESULT_EXTENSION_TIME)
    playedSegments: Optional[str] = Field(alias=CONTEXT_EXTENSION_PLAYED_SEGMENTS)


class VideoPausedResultExtensions(VideoResultExtensions):
    """Pydantic model for video paused `result`.`extensions` property.

    Attributes:
        progress (float): Consists of the ratio of media consumed by the actor.
    """

    progress: Optional[NonNegativeFloat] = Field(alias=RESULT_EXTENSION_PROGRESS)


class VideoSeekedResultExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for video seeked `result`.`extensions` property.

    Attributes:
        timeFrom (float): Consists of the point in time the actor changed from in a
            media object during a seek operation.
        timeTo (float): Consists of the point in time the actor changed to in a media
            object during a seek operation.
    """

    timeFrom: NonNegativeFloat = Field(alias=RESULT_EXTENSION_TIME_FROM)
    timeTo: NonNegativeFloat = Field(alias=RESULT_EXTENSION_TIME_TO)


class VideoCompletedResultExtensions(VideoResultExtensions):
    """Pydantic model for video completed `result`.`extensions` property.

    Attributes:
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    progress: NonNegativeFloat = Field(alias=RESULT_EXTENSION_PROGRESS)


class VideoTerminatedResultExtensions(VideoResultExtensions):
    """Pydantic model for video terminated `result`.`extensions` property.

    Attributes:
        progress (float): Consists of the percentage of media consumed by the actor.
    """

    progress: NonNegativeFloat = Field(alias=RESULT_EXTENSION_PROGRESS)


class VideoEnableClosedCaptioningResultExtensions(VideoResultExtensions):
    """Pydantic model for video enable closed captioning `result`.`extensions` property.

    Attributes:
        ccEnabled (bool): Indicates whether subtitles are enabled.
    """

    ccEnabled: bool = Field(alias=CONTEXT_EXTENSION_CC_ENABLED)


class VideoPlayedResult(BaseXapiResult):
    """Pydantic model for video played `result` property.

    Attributes:
        extensions (dict): See VideoResultExtensions.
    """

    extensions: VideoResultExtensions


class VideoPausedResult(BaseXapiResult):
    """Pydantic model for video paused `result` property.

    Attributes:
        extensions (dict): See VideoPausedResultExtensions.
    """

    extensions: VideoPausedResultExtensions


class VideoSeekedResult(BaseXapiResult):
    """Pydantic model for video seeked `result` property.

    Attributes:
        extensions (dict): See VideoSeekedResultExtensions.
    """

    extensions: VideoSeekedResultExtensions


class VideoCompletedResult(BaseXapiResult):
    """Pydantic model for video completed `result` property.

    Attributes:
        extensions (dict): See VideoCompletedResultExtensions.
        completion (bool): Consists of the value `True`.
        duration (str): Consists of the total time spent consuming the video under
            current registration.
    """

    extensions: VideoCompletedResultExtensions
    completion: Optional[Literal[True]] = None
    duration: Optional[timedelta] = None


class VideoTerminatedResult(BaseXapiResult):
    """Pydantic model for video terminated `result` property.

    Attributes:
        extensions (dict): See VideoTerminatedResultExtensions.
    """

    extensions: VideoTerminatedResultExtensions


class VideoEnableClosedCaptioningResult(BaseXapiResult):
    """Pydantic model for video enable closed captioning `result` property.

    Attributes:
        extensions (dict): See VideoEnableClosedCaptioningResultExtensions.
    """

    extensions: VideoEnableClosedCaptioningResultExtensions


class VideoVolumeChangeInteractionResult(BaseXapiResult):
    """Pydantic model for video volume change interaction `result` property.

    Attributes:
        extensions (dict): See VideoResultExtensions.
    """

    extensions: VideoResultExtensions


class VideoScreenChangeInteractionResult(BaseXapiResult):
    """Pydantic model for video screen change interaction `result` property.

    Attributes:
        extensions (dict): See VideoResultExtensions.
    """

    extensions: VideoResultExtensions
