"""Video xAPI events context fields definitions."""

from typing import Literal, Optional
from uuid import UUID

from pydantic import Field, NonNegativeFloat

from ...config import BaseExtensionModelWithConfig
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
    """Pydantic model for video `contextActivities` field.

    Attributes:
        category (list): Consists of a list containing the dictionary
            {"id": "https://w3id.org/xapi/video"}.
    """

    category: list[dict[Literal["id"], VIDEO_CONTEXT_CATEGORY]] = [
        {"id": VIDEO_CONTEXT_CATEGORY.__args__[0]}
    ]


class BaseVideoContextField(ContextField):
    """Pydantic model for video core `context` field.

    Attributes:
        contextActivities (dict): see VideoContextActivitiesField.
    """

    contextActivities: Optional[VideoContextActivitiesField]


class VideoContextExtensionsField(BaseExtensionModelWithConfig):
    """Pydantic model for video core `context`.`extensions` field.

    Attributes:
        session (uuid): Consists of the ID of the active session.
    """

    session_id: Optional[UUID] = Field(alias=VIDEO_EXTENSION_SESSION_ID)


class VideoInitializedContextExtensionsField(VideoContextExtensionsField):
    """Pydantic model for video initialized `context`.`extensions` field.

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
    """Pydantic model for video browsing `context`.`extensions` field.

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
    """Pydantic model for video volume change interaction `context`.`extensions` field.

    Attributes:
        volume (int): Consists of the volume of the video.
    """

    volume: int = Field(alias=VIDEO_EXTENSION_VOLUME)


class VideoScreenChangeInteractionContextExtensionsField(VideoContextExtensionsField):
    """Pydantic model for video screen change interaction `context`.`extensions` field.

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
    """Pydantic model for video initialized `context` field.

    Attributes:
        extensions (dict): See VideoInitializedContextExtensionsField.
    """

    extensions: VideoInitializedContextExtensionsField


class VideoPlayedContextField(BaseVideoContextField):
    """Pydantic model for video played `context` field.

    Attributes:
        extensions (dict): See VideoContextExtensionsField.
    """

    extensions: Optional[VideoContextExtensionsField]


class VideoPausedContextField(BaseVideoContextField):
    """Pydantic model for video paused `context` field.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
    """

    extensions: VideoBrowsingContextExtensionsField


class VideoSeekedContextField(BaseVideoContextField):
    """Pydantic model for video seeked `context` field.

    Attributes:
        extensions (dict): See VideoContextExtensionsField.
    """

    extensions: Optional[VideoContextExtensionsField]


class VideoCompletedContextField(BaseVideoContextField):
    """Pydantic model for video completed `context` field.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
    """

    extensions: VideoBrowsingContextExtensionsField


class VideoTerminatedContextField(BaseVideoContextField):
    """Pydantic model for video terminated `context` field.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
    """

    extensions: VideoBrowsingContextExtensionsField


class VideoEnableClosedCaptioningContextField(BaseVideoContextField):
    """Pydantic modle for video enable closed captioning `context` field.

    Attributes:
        extensions (dict): See VideoEnableClosedCaptioningContextExtensionsField.
    """

    extensions: VideoEnableClosedCaptioningContextExtensionsField


class VideoVolumeChangeInteractionContextField(BaseVideoContextField):
    """Pydantic model for video volume change interaction `context` field.

    Attributes:
        extensions (dict): See VideoVolumeChangeInteractionContextExtensionsField.
    """

    extensions: VideoVolumeChangeInteractionContextExtensionsField


class VideoScreenChangeInteractionContextField(BaseVideoContextField):
    """Pydantic model for video screen change interaction `context` field.

    Attributes:
        extensions (dict): See VideoScreenChangeInteractionContextExtensionsField.
    """

    extensions: VideoScreenChangeInteractionContextExtensionsField
