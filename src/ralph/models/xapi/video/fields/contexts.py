"""Video xAPI events context fields definitions"""

from typing import List, Literal, Optional

from pydantic import UUID4, Field

from ...base import BaseModelWithConfig
from ..constants import (
    VIDEO_CONTEXT_CATEGORY,
    VIDEO_EXTENSION_CC_SUBTITLE_ENABLED,
    VIDEO_EXTENSION_CC_SUBTITLE_LANG,
    VIDEO_EXTENSION_COMPLETION_THRESHOLD,
    VIDEO_EXTENSION_FRAME_RATE,
    VIDEO_EXTENSION_FULL_SCREEN,
    VIDEO_EXTENSION_LENGTH,
    VIDEO_EXTENSION_QUALITY,
    VIDEO_EXTENSION_SCREEN_SIZE,
    VIDEO_EXTENSION_SESSION_ID,
    VIDEO_EXTENSION_SPEED,
    VIDEO_EXTENSION_TRACK,
    VIDEO_EXTENSION_USER_AGENT,
    VIDEO_EXTENSION_VIDEO_PLAYBACK_SIZE,
    VIDEO_EXTENSION_VOLUME,
)


class VideoContextActivitiesField(BaseModelWithConfig):
    """Represents the contextActivities field for video xAPI statements.

    Attributes:
        category (list): Consists of a list containing the dictionary
            {"id": "https://w3id.org/xapi/video"}.
    """

    category: List[dict[Literal["id"], VIDEO_CONTEXT_CATEGORY]] = [
        {Literal["id"]: VIDEO_CONTEXT_CATEGORY.__args__[0]}
    ]


class BaseVideoContextField(BaseModelWithConfig):
    """Base model for xAPI video context field.

    Attributes:
        contextActivities (dict): see VideoContextActivitiesField.
    """

    contextActivities: Optional[VideoContextActivitiesField]


class VideoContextExtensionsField(BaseModelWithConfig):
    """Represents the common context.extensions field for video xAPI statement.

    Attributes:
        session (uuid5): Consists of the ID of the active session.
    """

    session: Optional[UUID4] = Field(alias=VIDEO_EXTENSION_SESSION_ID)


class VideoInitializedContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video `initialized` xAPI statement.

    Attributes:
        length (float): Consists of the length of the video.
        ccSubtitleEnabled (bool): Indicates whether subtitle or closed captioning is enabled.
        ccSubtitleLanguage (str): Consists of the language of subtitle or closed captioning.
        frameRate (float): Consists of the frame rate or frames per second of a video.
        fullScreen (bool): Indicates whether the video is played in full screen mode.
        quality (str): Consists of the video resolution or quality.
        screenSize (str): Consists of the device playback screen size or the maximum available
            screen size for Video playback.
        videoPlaybackSize (str): Consists of the size in Width x Height of the video as viewed
            by the user.
        speed (str): Consists of the play back speed.
        track (str): Consists of the name of the audio track in a media object.
        userAgent (str): Consists of the User Agent string of the browser,
            if the video is launched in browser.
        volume (int): Consists of the volume of the video.
        completionThreshold (float): Consists of the percentage of media that should be consumed to
            trigger a completion.
    """

    length: Optional[float] = Field(alias=VIDEO_EXTENSION_LENGTH)
    ccSubtitleEnabled: Optional[bool] = Field(alias=VIDEO_EXTENSION_CC_SUBTITLE_ENABLED)
    ccSubtitleLanguage: Optional[str] = Field(alias=VIDEO_EXTENSION_CC_SUBTITLE_LANG)
    frameRate: Optional[float] = Field(alias=VIDEO_EXTENSION_FRAME_RATE)
    fullScreen: Optional[bool] = Field(alias=VIDEO_EXTENSION_FULL_SCREEN)
    quality: Optional[str] = Field(alias=VIDEO_EXTENSION_QUALITY)
    screenSize: Optional[str] = Field(alias=VIDEO_EXTENSION_SCREEN_SIZE)
    videoPlaybackSize: Optional[str] = Field(alias=VIDEO_EXTENSION_VIDEO_PLAYBACK_SIZE)
    speed: Optional[str] = Field(alias=VIDEO_EXTENSION_SPEED)
    track: Optional[str] = Field(alias=VIDEO_EXTENSION_TRACK)
    userAgent: Optional[str] = Field(alias=VIDEO_EXTENSION_USER_AGENT)
    volume: Optional[int] = Field(alias=VIDEO_EXTENSION_VOLUME)
    completionThreshold: Optional[float] = Field(
        alias=VIDEO_EXTENSION_COMPLETION_THRESHOLD
    )


class VideoBrowsingContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video browsing xAPI statements.

    Such field is used in `paused`, `completed` and `terminated` events.

    Attributes:
        completionThreshold (float): Consists of the percentage of media that should be consumed to
            trigger a completion.
        length (float): Consists of the length of the video.
    """

    length: Optional[float] = Field(alias=VIDEO_EXTENSION_LENGTH)
    completionThreshold: Optional[float] = Field(
        alias=VIDEO_EXTENSION_COMPLETION_THRESHOLD
    )


class VideoInteractedContextExtensionsField(VideoContextExtensionsField):
    """Represents the context.extensions field for video `interacted` xAPI statement.

    Attributes:
        length (float): Consists of the length of the video.
        ccSubtitleEnabled (bool): Indicates whether subtitle or closed captioning is enabled.
        ccSubtitleLanguage (str): Consists of the language of subtitle or closed captioning.
        frameRate (float): Consists of the frame rate or frames per second of a video.
        fullScreen (bool): Indicates whether the video is played in full screen mode.
        quality (str): Consists of the video resolution or quality.
        videoPlaybackSize (str): Consists of the size in Width x Height of the video as viewed
            by the user.
        speed (str): Consists of the play back speed.
        track (str): Consists of the name of the audio track in a media object.
        volume (int): Consists of the volume of the video.
    """

    ccSubtitleEnabled: Optional[bool] = Field(alias=VIDEO_EXTENSION_CC_SUBTITLE_ENABLED)
    ccSubtitleLanguage: Optional[str] = Field(alias=VIDEO_EXTENSION_CC_SUBTITLE_LANG)
    frameRate: Optional[float] = Field(alias=VIDEO_EXTENSION_FRAME_RATE)
    fullScreen: Optional[bool] = Field(alias=VIDEO_EXTENSION_FULL_SCREEN)
    quality: Optional[str] = Field(alias=VIDEO_EXTENSION_QUALITY)
    videoPlaybackSize: Optional[str] = Field(alias=VIDEO_EXTENSION_VIDEO_PLAYBACK_SIZE)
    speed: Optional[str] = Field(alias=VIDEO_EXTENSION_SPEED)
    track: Optional[str] = Field(alias=VIDEO_EXTENSION_TRACK)
    volume: Optional[int] = Field(alias=VIDEO_EXTENSION_VOLUME)


class VideoInitializedContextField(BaseVideoContextField):
    """Represents the context field for video `initialized` xAPI statement.

    Attributes:
        extensions (dict): See VideoInitializedContextExtensionsField.
        contextActivities (dict): See VideoContextActivitiesField.
    """

    extensions: Optional[VideoInitializedContextExtensionsField]


class VideoPlayedContextField(BaseVideoContextField):
    """Represents the context field for video `played` xAPI statement.

    Attributes:
        extensions (dict): See VideoContextExtensionsField.
        contextActivities (dict): See VideoContextActivitiesField.
    """

    extensions: Optional[VideoContextExtensionsField]


class VideoPausedContextField(BaseVideoContextField):
    """Represents the context field for video `paused` xAPI statement.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
        contextActivities (dict): See VideoContextActivitiesField.
    """

    extensions: Optional[VideoBrowsingContextExtensionsField]


class VideoSeekedContextField(BaseVideoContextField):
    """Represents the context field for video `seeked` xAPI statement.

    Attributes:
        extensions (dict): See VideoContextExtensionsField.
        contextActivities (dict): See VideoContextActivitiesField.
    """

    extensions: Optional[VideoContextExtensionsField]


class VideoCompletedContextField(BaseVideoContextField):
    """Represents the context field for video `completed` xAPI statement.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
        contextActivities (dict): See VideoContextActivitiesField.
    """

    extensions: Optional[VideoBrowsingContextExtensionsField]


class VideoTerminatedContextField(BaseVideoContextField):
    """Represents the context field for video `terminated` xAPI statement.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensionsField.
        contextActivities (dict): See VideoContextActivitiesField.
    """

    extensions: Optional[VideoBrowsingContextExtensionsField]


class VideoInteractedContextField(BaseVideoContextField):
    """Represents the context field for video `interacted` xAPI statement.

    Attributes:
        extensions (dict): See VideoInteractedContextExtensionsField.
        contextActivities (dict): See VideoContextActivitiesField.
    """

    extensions: Optional[VideoInteractedContextExtensionsField]
