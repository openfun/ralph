"""Video event fields definitions."""

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ...base import AbstractBaseEventField


class VideoBaseEventField(AbstractBaseEventField):
    """Pydantic model for video core `event` field.

    Attributes:
        code (str): Consists of the `html5` value for browser-played
            videos.
        id (str): Consists of the additional videos name if given by the
            course creators, or the system-generated hash code otherwise.
    """

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = "allow"

    code: str
    id: str


class PlayVideoEventField(VideoBaseEventField):
    """Pydantic model for `play_video`.`event` field.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float


class PauseVideoEventField(VideoBaseEventField):
    """Pydantic model for `pause_video`.`event`.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float


class SeekVideoEventField(VideoBaseEventField):
    """Pydantic model for `seek_video`.`event` field.

    Attributes:
        new_time (float): Consists of the point in time the actor changed to in a media
            object during a seek operation.
        old_time (float): Consists of the point in time the actor changed from in a
            media object during a seek operation.
        type (str): Consists of the navigational method used to change position
            within the video, either `onCaptionSeek` or `onSlideSeek` value.
    """

    new_time: float
    old_time: float
    type: str


class StopVideoEventField(VideoBaseEventField):
    """Pydantic model for `stop_video`.`event` field.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float


class VideoHideTranscriptEventField(VideoBaseEventField):
    """Pydantic model for `hide_transcript`.`event` field.

    Attributes:
        current_time (float): Consists of the time in the video at which
            the statement was emitted.
    """

    current_time: float


class VideoShowTranscriptEventField(VideoBaseEventField):
    """Pydantic model for `show_transcript`.`event` field.

    Attributes:
        current_time (float): Consists of the time in the video at which
            the statement was emitted.
    """

    current_time: float


class SpeedChangeVideoEventField(VideoBaseEventField):
    """Pydantic model for `speed_change_video`.`event` field.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float
    new_speed: Literal["0.75", "1.0", "1.25", "1.50", "2.0"]
    old_speed: Literal["0.75", "1.0", "1.25", "1.50", "2.0"]
