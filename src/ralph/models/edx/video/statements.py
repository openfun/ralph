"""Video event model definitions"""

from typing import Literal, Optional, Union

from pydantic import Json

from ralph.models.edx.video.fields.events import (
    PauseVideoEventField,
    PlayVideoEventField,
    SeekVideoEventField,
    SpeedChangeVideoEventField,
    StopVideoEventField,
    VideoBaseEventField,
    VideoTranscriptEventField,
)
from ralph.models.selector import selector

from ..browser import BaseBrowserModel


class UILoadVideo(BaseBrowserModel):
    """Represents the `load_video` event model.

    Attributes:
        event (VideoBaseEventField): See VideoBaseEventField.
        event_type (str): Consists of the value `load_video`.
        name (str): Consists either of the value `load_video` or `edx.video.loaded`.
    """

    __selector__ = selector(event_source="browser", event_type="load_video")

    event: Union[
        Json[VideoBaseEventField],  # pylint: disable=unsubscriptable-object
        VideoBaseEventField,
    ]
    event_type: Literal["load_video"]
    name: Literal["load_video", "edx.video.loaded"]


class UIPlayVideo(BaseBrowserModel):
    """Represents the `play_video` event model.

    Attributes:
        event (PlayVideoEventField): See PlayVideoEventField.
        event_type (str): Consists of the value `play_video`.
        name (str): Consists either of the value `play_video` or `edx.video.played`.
    """

    __selector__ = selector(event_source="browser", event_type="play_video")

    event: Union[
        Json[PlayVideoEventField],  # pylint: disable=unsubscriptable-object
        PlayVideoEventField,
    ]
    event_type: Literal["play_video"]
    name: Optional[Literal["play_video", "edx.video.played"]]


class UIPauseVideo(BaseBrowserModel):
    """Represents the `pause_video` event model.

    Attributes:
        event (PauseVideoEventField): See PauseVideoEventField.
        event_type (str): Consists of the value `pause_video`.
        name (str): Consists either of the value `pause_video` or `edx.video.paused`.
    """

    __selector__ = selector(event_source="browser", event_type="pause_video")

    event: Union[
        Json[PauseVideoEventField],  # pylint: disable=unsubscriptable-object
        PauseVideoEventField,
    ]
    event_type: Literal["pause_video"]
    name: Optional[Literal["pause_video", "edx.video.paused"]]


class UISeekVideo(BaseBrowserModel):
    """Represents the `seek_video` event model.

    Attributes:
        event (SeekVideoEventField): See SeekVideoEventField.
        event_type (str): Consists of the value `seek_video`.
        name (str): Consists either of the value `seek_video` or
            `edx.video.position.changed`.
    """

    __selector__ = selector(event_source="browser", event_type="seek_video")

    event: Union[
        Json[SeekVideoEventField],  # pylint: disable=unsubscriptable-object
        SeekVideoEventField,
    ]
    event_type: Literal["seek_video"]
    name: Optional[Literal["seek_video", "edx.video.position.changed"]]


class UIStopVideo(BaseBrowserModel):
    """Represents the `stop_video` event model.

    Attributes:
        event (StopVideoEventField): See StopVideoEventField.
        event_type (str): Consists of the value `stop_video`.
        name (str): Consists either of the value `stop_video` or `edx.video.stopped`.
    """

    __selector__ = selector(event_source="browser", event_type="stop_video")

    event: Union[
        Json[StopVideoEventField],  # pylint: disable=unsubscriptable-object
        StopVideoEventField,
    ]
    event_type: Literal["stop_video"]
    name: Optional[Literal["stop_video", "edx.video.stopped"]]


class UIHideTranscript(BaseBrowserModel):
    """Represents the `hide_transcript` event model.

    Attributes:
        event (VideoTranscriptEventField): See VideoTranscriptEventField.
        event_type (str): Consists of the value `hide_transcript`.
        name (str): Consists either of the value `hide_transcript` or
            `edx.video.transcript.hidden`.
    """

    __selector__ = selector(event_source="browser", event_type="hide_transcript")

    event: Union[
        Json[VideoTranscriptEventField],  # pylint: disable=unsubscriptable-object
        VideoTranscriptEventField,
    ]
    event_type: Literal["hide_transcript"]
    name: Literal["hide_transcript", "edx.video.transcript.hidden"]


class UIShowTranscript(BaseBrowserModel):
    """Represents the `show_transcript` event model.

    Attributes:
        event (VideoTranscriptEventField): See VideoTranscriptEventField.
        event_type (str): Consists of the value `show_transcript`.
        name (str): Consists either of the value `show_transcript` or
            `edx.video.transcript.shown`.
    """

    __selector__ = selector(event_source="browser", event_type="show_transcript")

    event: Union[
        Json[VideoTranscriptEventField],  # pylint: disable=unsubscriptable-object
        VideoTranscriptEventField,
    ]
    event_type: Literal["show_transcript"]
    name: Literal["show_transcript", "edx.video.transcript.shown"]


class UISpeedChangeVideo(BaseBrowserModel):
    """Represents the `speed_change_video` event model.

    Attributes:
        event (SpeedChangeVideoEventField): See SpeedChangeVideoEventField.
        event_type (str): Consists of the value `speed_change_video`.
    """

    __selector__ = selector(event_source="browser", event_type="speed_change_video")

    event: Union[
        Json[SpeedChangeVideoEventField],  # pylint: disable=unsubscriptable-object
        SpeedChangeVideoEventField,
    ]
    event_type: Literal["speed_change_video"]
    name: Optional[Literal["speed_change_video"]]


class UIVideoHideCCMenu(BaseBrowserModel):
    """Represents the `video_hide_cc_menu` event model.

    Attributes:
        event (VideoBaseEventField): See VideoBaseEventField.
        event_type (str): Consists of the value `video_hide_cc_menu`.
    """

    __selector__ = selector(event_source="browser", event_type="video_hide_cc_menu")

    event: Union[
        Json[VideoBaseEventField],  # pylint: disable=unsubscriptable-object
        VideoBaseEventField,
    ]
    event_type: Literal["video_hide_cc_menu"]
    name: Optional[Literal["video_hide_cc_menu"]]


class UIVideoShowCCMenu(BaseBrowserModel):
    """Represents the `video_show_cc_menu` event model.

    Attributes:
        event (VideoBaseEventField): See VideoBaseEventField.
        event_type (str): Consists of the value `video_show_cc_menu`.
    """

    __selector__ = selector(event_source="browser", event_type="video_show_cc_menu")

    event: Union[
        Json[VideoBaseEventField],  # pylint: disable=unsubscriptable-object
        VideoBaseEventField,
    ]
    event_type: Literal["video_show_cc_menu"]
    name: Optional[Literal["video_show_cc_menu"]]
