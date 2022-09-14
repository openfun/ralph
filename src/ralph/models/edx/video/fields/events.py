"""Video event fields definitions."""

from typing import Literal

from ...base import AbstractBaseEventField


class VideoBaseEventField(AbstractBaseEventField):
    """Represents the event field which attributes are common to most
    of the video statements.

    Attributes:
        code (str): Consists of the `html5` value for browser-played
            videos.
        id (str): Consists of the additional videos name if given by the
            course creators, or the system-generated hash code otherwise.
    """

    class Config:  # pylint: disable=missing-class-docstring
        extra = "allow"

    code: str
    id: str


class PlayVideoEventField(VideoBaseEventField):
    """Represents the event field of `play_video` statement.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float


class PauseVideoEventField(VideoBaseEventField):
    """Represents the event field of `pause_video` statement.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float


class SeekVideoEventField(VideoBaseEventField):
    """Represents the event field of `seek_video` statement.

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
    """Represents the event field of `stop_video` statement.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float


class VideoTranscriptEventField(VideoBaseEventField):
    """Represents the event field of `hide_transcript` and `show_transcript`
    statement.

    Attributes:
        current_time (float): Consists of the time in the video at which
            the statement was emitted.
    """

    current_time: float


class SpeedChangeVideoEventField(VideoBaseEventField):
    """Represents the event field of `speed_change_video` statement.

    Attributes:
        currentTime (float): Consists of the time in the video at which
            the statement was emitted.
    """

    currentTime: float
    new_speed: Literal["0.75", "1.0", "1.25", "1.50", "2.0"]
    old_speed: Literal["0.75", "1.0", "1.25", "1.50", "2.0"]
