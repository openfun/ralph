"""Video xAPI events context fields definitions."""

import sys
from typing import List, Optional, Union
from uuid import UUID

from pydantic import Field, NonNegativeFloat, field_validator
from typing_extensions import Annotated

from ..base.contexts import BaseXapiContext, BaseXapiContextContextActivities
from ..base.unnested_objects import BaseXapiActivity
from ..concepts.activity_types.scorm_profile import ProfileActivity
from ..concepts.constants.video import (
    CONTEXT_EXTENSION_CC_ENABLED,
    CONTEXT_EXTENSION_CC_SUBTITLE_LANG,
    CONTEXT_EXTENSION_COMPLETION_THRESHOLD,
    CONTEXT_EXTENSION_FULL_SCREEN,
    CONTEXT_EXTENSION_LENGTH,
    CONTEXT_EXTENSION_SCREEN_SIZE,
    CONTEXT_EXTENSION_SESSION_ID,
    CONTEXT_EXTENSION_SPEED,
    CONTEXT_EXTENSION_USER_AGENT,
    CONTEXT_EXTENSION_VIDEO_PLAYBACK_SIZE,
    CONTEXT_EXTENSION_VOLUME,
)
from ..config import BaseExtensionModelWithConfig

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class VideoProfileActivity(ProfileActivity):
    """Pydantic model for video profile `Activity` type.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video`.
    """

    id: Literal["https://w3id.org/xapi/video"] = "https://w3id.org/xapi/video"


class VideoContextContextActivities(BaseXapiContextContextActivities):
    """Pydantic model for video `context`.`contextActivities` property.

    Attributes:
        category (dict or list): see VideoProfileActivity.
    """

    category: Union[
        VideoProfileActivity, List[Union[VideoProfileActivity, BaseXapiActivity]]
    ]

    @field_validator("category")
    @classmethod
    def check_presence_of_profile_activity_category(
        cls,
        value: Union[
            VideoProfileActivity, List[Union[VideoProfileActivity, BaseXapiActivity]]
        ],
    ) -> Union[
        VideoProfileActivity, List[Union[VideoProfileActivity, BaseXapiActivity]]
    ]:
        """Check that the category list contains a `VideoProfileActivity`."""
        if isinstance(value, VideoProfileActivity):
            return value
        for activity in value:
            if isinstance(activity, VideoProfileActivity):
                return value
        raise ValueError(
            "The `context.contextActivities.category` field should contain at least "
            "one valid `VideoProfileActivity`"
        )


class BaseVideoContext(BaseXapiContext):
    """Pydantic model for video core `context` property.

    Attributes:
        contextActivities (dict): see VideoContextContextActivities.
    """

    contextActivities: VideoContextContextActivities


class VideoContextExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for video core context `extensions` property.

    Attributes:
        session (uuid): Consists of the ID of the active session.
    """

    session_id: Annotated[Optional[UUID], Field(alias=CONTEXT_EXTENSION_SESSION_ID)]


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

    length: Annotated[NonNegativeFloat, Field(alias=CONTEXT_EXTENSION_LENGTH)]
    ccSubtitleEnabled: Annotated[
        Optional[bool], Field(alias=CONTEXT_EXTENSION_CC_ENABLED)
    ] = None
    ccSubtitleLang: Annotated[
        Optional[str], Field(alias=CONTEXT_EXTENSION_CC_SUBTITLE_LANG)
    ] = None
    fullScreen: Annotated[
        Optional[bool], Field(alias=CONTEXT_EXTENSION_FULL_SCREEN)
    ] = None
    screenSize: Annotated[Optional[str], Field(alias=CONTEXT_EXTENSION_SCREEN_SIZE)] = (
        None
    )
    videoPlaybackSize: Annotated[
        Optional[str], Field(alias=CONTEXT_EXTENSION_VIDEO_PLAYBACK_SIZE)
    ] = None
    speed: Annotated[Optional[str], Field(alias=CONTEXT_EXTENSION_SPEED)] = None
    userAgent: Annotated[Optional[str], Field(alias=CONTEXT_EXTENSION_USER_AGENT)] = (
        None
    )
    volume: Annotated[Optional[int], Field(alias=CONTEXT_EXTENSION_VOLUME)] = None
    completionThreshold: Annotated[
        Optional[float], Field(alias=CONTEXT_EXTENSION_COMPLETION_THRESHOLD)
    ] = None


class VideoBrowsingContextExtensions(VideoContextExtensions):
    """Pydantic model for video browsing `context`.`extensions` property.

    Such field is used in `paused`, `completed` and `terminated` events.

    Attributes:
        completionThreshold (float): Consists of the percentage of media that should
            be consumed to trigger a completion.
        length (float): Consists of the length of the video.
    """

    length: Annotated[NonNegativeFloat, Field(alias=CONTEXT_EXTENSION_LENGTH)]
    completionThreshold: Annotated[
        Optional[float], Field(alias=CONTEXT_EXTENSION_COMPLETION_THRESHOLD)
    ] = None


class VideoEnableClosedCaptioningContextExtensions(VideoContextExtensions):
    """Represents the context.extensions field for video `interacted` xAPI statement.

    Attributes:
        ccSubtitleLanguage (str): Consists of the language of subtitle or closed
            captioning.
    """

    ccSubtitleLanguage: Annotated[str, Field(alias=CONTEXT_EXTENSION_CC_SUBTITLE_LANG)]


class VideoVolumeChangeInteractionContextExtensions(VideoContextExtensions):
    """Pydantic model for video volume change interaction `context`.`extensions`
    property.

    Attributes:
        volume (int): Consists of the volume of the video.
    """  # noqa: D205

    volume: Annotated[int, Field(alias=CONTEXT_EXTENSION_VOLUME)]


class VideoScreenChangeInteractionContextExtensions(VideoContextExtensions):
    """Pydantic model for video screen change interaction `context`.`extensions`
    property.

    Attributes:
        fullScreen (bool): Indicates whether the video is played in full screen mode.
        screenSize (str): Expresses the total available screen size for Video playback.
        videoPlaybackSize (str): Consists of the size in Width x Height of the video as
            viewed by the user.
    """  # noqa: D205

    fullScreen: Annotated[bool, Field(alias=CONTEXT_EXTENSION_FULL_SCREEN)]
    screenSize: Annotated[str, Field(alias=CONTEXT_EXTENSION_SCREEN_SIZE)]
    videoPlaybackSize: Annotated[
        str, Field(alias=CONTEXT_EXTENSION_VIDEO_PLAYBACK_SIZE)
    ]


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

    extensions: Optional[VideoContextExtensions] = None


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

    extensions: Optional[VideoContextExtensions] = None


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
