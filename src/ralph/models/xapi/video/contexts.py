"""Video xAPI events context fields definitions."""

from typing import List, Optional, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from uuid import UUID

from pydantic import Field, NonNegativeFloat, PositiveInt

from ..base.contexts import BaseXapiContext, BaseXapiContextContextActivities
from ..base.unnested_objects import BaseXapiActivity
from ..concepts.activity_types.scorm_profile import ProfileActivity
from ..concepts.constants.video import (
    CONTEXT_EXTENSION_CC_ENABLED,
    CONTEXT_EXTENSION_CC_SUBTITLE_LANG,
    CONTEXT_EXTENSION_COMPLETION_THRESHOLD,
    CONTEXT_EXTENSION_FULL_SCREEN,
    CONTEXT_EXTENSION_LENGTH,
    CONTEXT_EXTENSION_QUALITY,
    CONTEXT_EXTENSION_SCREEN_SIZE,
    CONTEXT_EXTENSION_SESSION_ID,
    CONTEXT_EXTENSION_SPEED,
    CONTEXT_EXTENSION_USER_AGENT,
    CONTEXT_EXTENSION_VIDEO_PLAYBACK_SIZE,
    CONTEXT_EXTENSION_VOLUME,
)
from ..config import BaseExtensionModelWithConfig


class VideoContextContextActivitiesCategory(BaseXapiActivity):
    # noqa: D205, D415
    """Pydantic model for video `context`.`contextActivities`.`category`
    property.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video`.
        definition (dict): see ProfileActivity.
    """

    id: Literal["https://w3id.org/xapi/video"] = "https://w3id.org/xapi/video"
    definition: ProfileActivity


class VideoContextContextActivities(BaseXapiContextContextActivities):
    """Pydantic model for video `context`.`contextActivities` property.

    Attributes:
        category (list): see VideoContextContextActivitiesCategory.
    """

    category: Union[
        VideoContextContextActivitiesCategory,
        List[VideoContextContextActivitiesCategory],
    ]


class BaseVideoContext(BaseXapiContext):
    """Pydantic model for video core `context` property.

    Attributes:
        contextActivities (dict): see VideoContextContextActivities.
    """

    contextActivities: Optional[VideoContextContextActivities]


class VideoContextExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for video core context `extensions` property.

    Attributes:
        session (uuid): Consists of the ID of the active session.
    """

    session_id: Optional[UUID] = Field(alias=CONTEXT_EXTENSION_SESSION_ID)


class VideoInitializedContextExtensions(VideoContextExtensions):
    """Pydantic model for video initialized `context` `extensions` property.

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

    length: NonNegativeFloat = Field(alias=CONTEXT_EXTENSION_LENGTH)
    ccSubtitleEnabled: Optional[bool] = Field(alias=CONTEXT_EXTENSION_CC_ENABLED)
    ccSubtitleLang: Optional[str] = Field(alias=CONTEXT_EXTENSION_CC_SUBTITLE_LANG)
    fullScreen: Optional[bool] = Field(alias=CONTEXT_EXTENSION_FULL_SCREEN)
    screenSize: Optional[str] = Field(alias=CONTEXT_EXTENSION_SCREEN_SIZE)
    videoPlaybackSize: Optional[str] = Field(
        alias=CONTEXT_EXTENSION_VIDEO_PLAYBACK_SIZE
    )
    speed: Optional[str] = Field(alias=CONTEXT_EXTENSION_SPEED)
    userAgent: Optional[str] = Field(alias=CONTEXT_EXTENSION_USER_AGENT)
    volume: Optional[int] = Field(alias=CONTEXT_EXTENSION_VOLUME)
    completionThreshold: Optional[float] = Field(
        alias=CONTEXT_EXTENSION_COMPLETION_THRESHOLD
    )


class VideoBrowsingContextExtensions(VideoContextExtensions):
    """Pydantic model for video browsing `context`.`extensions` property.

    Such field is used in `paused`, `completed` and `terminated` events.

    Attributes:
        completionThreshold (float): Consists of the percentage of media that should
            be consumed to trigger a completion.
        length (float): Consists of the length of the video.
    """

    length: NonNegativeFloat = Field(alias=CONTEXT_EXTENSION_LENGTH)
    completionThreshold: Optional[float] = Field(
        alias=CONTEXT_EXTENSION_COMPLETION_THRESHOLD
    )


class VideoDownloadedContextExtensions(VideoContextExtensions):
    """Represents the context.extensions field for video `downloaded` xAPI statement.

    Attributes:
        length (float): Consists of the length of the video.
        quality (int): Consists of the video resolution or quality of the video.
        session (uuid): Consists of the ID of the active session.
    """

    length: NonNegativeFloat = Field(alias=CONTEXT_EXTENSION_LENGTH)
    quality: PositiveInt = Field(alias=CONTEXT_EXTENSION_QUALITY)
    session_id: Optional[UUID] = Field(alias=CONTEXT_EXTENSION_SESSION_ID)


class VideoEnableClosedCaptioningContextExtensions(VideoContextExtensions):
    """Represents the context.extensions field for video `interacted` xAPI statement.

    Attributes:
        ccSubtitleLanguage (str): Consists of the language of subtitle or closed
            captioning.
    """

    ccSubtitleLanguage: str = Field(alias=CONTEXT_EXTENSION_CC_SUBTITLE_LANG)


class VideoVolumeChangeInteractionContextExtensions(VideoContextExtensions):
    # noqa: D205, D415
    """Pydantic model for video volume change interaction `context`.`extensions`
    property.

    Attributes:
        volume (int): Consists of the volume of the video.
    """

    volume: int = Field(alias=CONTEXT_EXTENSION_VOLUME)


class VideoScreenChangeInteractionContextExtensions(VideoContextExtensions):
    # noqa: D205, D415
    """Pydantic model for video screen change interaction `context`.`extensions`
    property.

    Attributes:
        fullScreen (bool): Indicates whether the video is played in full screen mode.
        screenSize (str): Expresses the total available screen size for Video playback.
        videoPlaybackSize (str): Consists of the size in Width x Height of the video as
            viewed by the user.
    """

    fullScreen: bool = Field(alias=CONTEXT_EXTENSION_FULL_SCREEN)
    screenSize: str = Field(alias=CONTEXT_EXTENSION_SCREEN_SIZE)
    videoPlaybackSize: str = Field(alias=CONTEXT_EXTENSION_VIDEO_PLAYBACK_SIZE)


class VideoInitializedContext(BaseVideoContext):
    """Pydantic model for video initialized `context` property.

    Attributes:
        extensions (dict): See VideoInitializedContextExtensions.
    """

    extensions: VideoInitializedContextExtensions


class VideoPlayedContext(BaseVideoContext):
    """Pydantic model for video played `context` property.

    Attributes:
        extensions (dict): See VideoContextExtensions.
    """

    extensions: Optional[VideoContextExtensions]


class VideoPausedContext(BaseVideoContext):
    """Pydantic model for video paused `context` property.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensions.
    """

    extensions: VideoBrowsingContextExtensions


class VideoSeekedContext(BaseVideoContext):
    """Pydantic model for video seeked `context` property.

    Attributes:
        extensions (dict): See VideoContextExtensions.
    """

    extensions: Optional[VideoContextExtensions]


class VideoCompletedContext(BaseVideoContext):
    """Pydantic model for video completed `context` property.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensions.
    """

    extensions: VideoBrowsingContextExtensions


class VideoTerminatedContext(BaseVideoContext):
    """Pydantic model for video terminated `context` property.

    Attributes:
        extensions (dict): See VideoBrowsingContextExtensions.
    """

    extensions: VideoBrowsingContextExtensions


class VideoDownloadedContext(BaseVideoContext):
    """Pydantic model for video downloaded `context` property.

    Attributes:
        extensions (dict): See VideoDownloadedContextExtensions.
    """

    extensions: VideoDownloadedContextExtensions


class VideoEnableClosedCaptioningContext(BaseVideoContext):
    """Pydantic model for video enable closed captioning `context` property.

    Attributes:
        extensions (dict): See VideoEnableClosedCaptioningContextExtensions.
    """

    extensions: VideoEnableClosedCaptioningContextExtensions


class VideoVolumeChangeInteractionContext(BaseVideoContext):
    """Pydantic model for video volume change interaction `context` property.

    Attributes:
        extensions (dict): See VideoVolumeChangeInteractionContextExtensions.
    """

    extensions: VideoVolumeChangeInteractionContextExtensions


class VideoScreenChangeInteractionContext(BaseVideoContext):
    """Pydantic model for video screen change interaction `context` property.

    Attributes:
        extensions (dict): See VideoScreenChangeInteractionContextExtensions.
    """

    extensions: VideoScreenChangeInteractionContextExtensions
