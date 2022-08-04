"""Video xAPI events context fields definitions"""

from typing import Literal, Optional
from uuid import UUID

from pydantic import Field, NonNegativeFloat

from ...base import BaseModelWithConfig
from ...fields.contexts import ContextActivitiesContextField, ContextField
from ..constants import (
    VIDEO_CONTEXT_CATEGORY,
    VIDEO_EXTENSION_CC_ENABLED,
    VIDEO_EXTENSION_CC_SUBTITLE_LANG,
    VIDEO_EXTENSION_COMPLETION_THRESHOLD,
    VIDEO_EXTENSION_FULL_SCREEN,
    VIDEO_EXTENSION_LENGTH,
    VIDEO_EXTENSION_SCREEN_SIZE,
    VIDEO_EXTENSION_SESSION_ID,
    VIDEO_EXTENSION_SPEED,
    VIDEO_EXTENSION_USER_AGENT,
    VIDEO_EXTENSION_VIDEO_PLAYBACK_SIZE,
    VIDEO_EXTENSION_VOLUME,
)


class VideoContextActivitiesField(ContextActivitiesContextField):
    """Represents the contextActivities field for video xAPI statements.

    Attributes:
        category (list): Consists of a list containing the dictionary
            {"id": "https://w3id.org/xapi/video"}.
    """

    category: list[dict[Literal["id"], VIDEO_CONTEXT_CATEGORY]] = [
        {"id": VIDEO_CONTEXT_CATEGORY.__args__[0]}
    ]


class BaseVideoContextField(ContextField):
    """Base model for xAPI video context field.

    Attributes:
        contextActivities (dict): see VideoContextActivitiesField.
    """

    contextActivities: Optional[VideoContextActivitiesField]


class VideoContextExtensionsField(BaseModelWithConfig):
    """Represents the common context.extensions field for video xAPI statement.

    Attributes:
        session (uuid): Consists of the ID of the active session.
    """

    session_id: Optional[UUID] = Field(alias=VIDEO_EXTENSION_SESSION_ID)


class VideoInitializedContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video `initialized` xAPI statement.

    Attributes:
        length (float): Consists of the length of the video.
        ccSubtitleEnabled (bool): Indicates whether subtitle or closed captioning is
            enabled.
        ccSubtitleLanguage (str): Consists of the language of subtitle or closed
            captioning.
        fullScreen (bool): Indicates whether the video is played in full screen mode.
        screenSize (str): Consists of the device playback screen size or the maximum
            available screen size for Video playback.
        videoPlaybackSize (str): Consists of the size in Width x Height of the video as
            viewed by the user.
        speed (str): Consists of the play back speed.
        userAgent (str): Consists of the User Agent string of the browser,
            if the video is launched in browser.
        volume (int): Consists of the volume of the video.
        completionThreshold (float): Consists of the percentage of media that should be
            consumed to trigger a completion.
    """

    length: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_LENGTH)
    ccSubtitleEnabled: Optional[bool] = Field(alias=VIDEO_EXTENSION_CC_ENABLED)
    ccSubtitleLang: Optional[str] = Field(alias=VIDEO_EXTENSION_CC_SUBTITLE_LANG)
    fullScreen: Optional[bool] = Field(alias=VIDEO_EXTENSION_FULL_SCREEN)
    screenSize: Optional[str] = Field(alias=VIDEO_EXTENSION_SCREEN_SIZE)
    videoPlaybackSize: Optional[str] = Field(alias=VIDEO_EXTENSION_VIDEO_PLAYBACK_SIZE)
    speed: Optional[str] = Field(alias=VIDEO_EXTENSION_SPEED)
    userAgent: Optional[str] = Field(alias=VIDEO_EXTENSION_USER_AGENT)
    volume: Optional[int] = Field(alias=VIDEO_EXTENSION_VOLUME)
    completionThreshold: Optional[float] = Field(
        alias=VIDEO_EXTENSION_COMPLETION_THRESHOLD
    )


class VideoBrowsingContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video browsing xAPI statements.

    Such field is used in `paused`, `completed` and `terminated` events.

    Attributes:
        completionThreshold (float): Consists of the percentage of media that should
            be consumed to trigger a completion.
        length (float): Consists of the length of the video.
    """

    length: NonNegativeFloat = Field(alias=VIDEO_EXTENSION_LENGTH)
    completionThreshold: Optional[float] = Field(
        alias=VIDEO_EXTENSION_COMPLETION_THRESHOLD
    )


class VideoEnableClosedCaptioningContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video `interacted` xAPI statement.

    Attributes:
        ccSubtitleLanguage (str): Consists of the language of subtitle or closed
            captioning.
    """

    ccSubtitleLanguage: str = Field(alias=VIDEO_EXTENSION_CC_SUBTITLE_LANG)


class VideoVolumeChangeInteractionContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video volume change interaction xAPI
    statement.

    Attributes:
        volume (int): Consists of the volume of the video.
    """

    volume: int = Field(alias=VIDEO_EXTENSION_VOLUME)


class VideoScreenChangeInteractionContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video screen change interaction xAPI
    statement.

    Attributes:
        fullScreen (bool): Indicates whether the video is played in full screen mode.
        screenSize (str): Expresses the total available screen size for Video playback.
        videoPlaybackSize (str): Consists of the size in Width x Height of the video as
            viewed by the user.
    """

    fullScreen: bool = Field(alias=VIDEO_EXTENSION_FULL_SCREEN)
    screenSize: str = Field(alias=VIDEO_EXTENSION_SCREEN_SIZE)
    videoPlaybackSize: str = Field(alias=VIDEO_EXTENSION_VIDEO_PLAYBACK_SIZE)


class VideoInitializedContextField(BaseVideoContextField):
    """Represents the context field for video `initialized` xAPI statement.

    Attributes:
        extensions (dict): See VideoInitializedContextExtensionsField.
    """

    extensions: VideoInitializedContextExtensionsField


class VideoPlayedContextField(BaseVideoContextField):
    """Represents the context field for video `played` xAPI statement.

    Attributes:
        extensions (dict): See VideoContextExtensionsField.
    """

    extensions: Optional[VideoContextExtensionsField]


class VideoPausedContextField(BaseVideoContextField):
    """Represents the context field for video `paused` xAPI statement.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
    """

    extensions: VideoBrowsingContextExtensionsField


class VideoSeekedContextField(BaseVideoContextField):
    """Represents the context field for video `seeked` xAPI statement.

    Attributes:
        extensions (dict): See VideoContextExtensionsField.
    """

    extensions: Optional[VideoContextExtensionsField]


class VideoCompletedContextField(BaseVideoContextField):
    """Represents the context field for video `completed` xAPI statement.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
    """

    extensions: VideoBrowsingContextExtensionsField


class VideoTerminatedContextField(BaseVideoContextField):
    """Represents the context field for video `terminated` xAPI statement.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
    """

    extensions: VideoBrowsingContextExtensionsField


class VideoEnableClosedCaptioningContextField(BaseVideoContextField):
    """Represents the context field for video enable closed captioning xAPI statement.

    Attributes:
        extensions (dict): See VideoEnableClosedCaptioningContextExtensionsField.
    """

    extensions: VideoEnableClosedCaptioningContextExtensionsField


class VideoVolumeChangeInteractionContextField(BaseVideoContextField):
    """Represents the context field for video volume change interaction xAPI
    statement.

    Attributes:
        extensions (dict): See VideoVolumeChangeInteractionContextExtensionsField.
    """

    extensions: VideoVolumeChangeInteractionContextExtensionsField


class VideoScreenChangeInteractionContextField(BaseVideoContextField):
    """Represents the context field for video screen change interaction xAPI
    statement.

    Attributes:
        extensions (dict): See VideoScreenChangeInteractionContextExtensionsField.
    """

    extensions: VideoScreenChangeInteractionContextExtensionsField
