"""Video event xAPI Converter."""

from ralph.models.converter import ConversionItem
from ralph.models.edx.video.statements import (
    UILoadVideo,
    UIPauseVideo,
    UIPlayVideo,
    UISeekVideo,
    UIStopVideo,
)
from ralph.models.xapi.constants import LANG_EN_US_DISPLAY
from ralph.models.xapi.video.constants import (
    VIDEO_EXTENSION_LENGTH,
    VIDEO_EXTENSION_PROGRESS,
    VIDEO_EXTENSION_SESSION_ID,
    VIDEO_EXTENSION_TIME,
    VIDEO_EXTENSION_TIME_FROM,
    VIDEO_EXTENSION_TIME_TO,
    VIDEO_EXTENSION_USER_AGENT,
)
from ralph.models.xapi.video.statements import (
    VideoInitialized,
    VideoPaused,
    VideoPlayed,
    VideoSeeked,
    VideoTerminated,
)

from .base import BaseXapiConverter


class VideoBaseXapiConverter(BaseXapiConverter):
    """Base Video xAPI Converter."""

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "object__definition__name",
                    "event__id",
                    lambda id: {LANG_EN_US_DISPLAY.__args__[0]: id},
                ),
                ConversionItem(
                    "object__id",
                    None,
                    lambda event: self.platform_url
                    + "/xblock/block-v1:"
                    + event["context"]["course_id"]
                    + "-course-v1:+type@video+block@"
                    + event["event"]["id"],
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UILoadVideoToVideoInitialized(VideoBaseXapiConverter):
    """Converts a common edX `load_video` event to xAPI."""

    __src__ = UILoadVideo
    __dest__ = VideoInitialized

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_LENGTH,
                    None,
                    # Set the video length to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `load_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_SESSION_ID,
                    "session",
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_USER_AGENT, "agent"
                ),
            },
        )


class UIPlayVideoToVideoPlayed(VideoBaseXapiConverter):
    """Converts a common edX `play_video` event to xAPI."""

    __src__ = UIPlayVideo
    __dest__ = VideoPlayed

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + VIDEO_EXTENSION_TIME,
                    "event__currentTime",
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UIPauseVideoToVideoPaused(VideoBaseXapiConverter):
    """Converts a common edX `pause_video` event to xAPI."""

    __src__ = UIPauseVideo
    __dest__ = VideoPaused

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + VIDEO_EXTENSION_TIME,
                    "event__currentTime",
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_LENGTH,
                    None,
                    # Set the video length to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `pause_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UIStopVideoToVideoTerminated(VideoBaseXapiConverter):
    """Converts a common edX `stop_video` event to xAPI."""

    __src__ = UIStopVideo
    __dest__ = VideoTerminated

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + VIDEO_EXTENSION_TIME,
                    "event__currentTime",
                ),
                ConversionItem(
                    "result__extensions__" + VIDEO_EXTENSION_PROGRESS,
                    None,
                    # Set the video progress to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `stop_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_LENGTH,
                    None,
                    # Set the video length to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `stop_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UISeekVideoToVideoSeeked(VideoBaseXapiConverter):
    """Converts a common edX `seek_video` event to xAPI."""

    __src__ = UISeekVideo
    __dest__ = VideoSeeked

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + VIDEO_EXTENSION_TIME_FROM,
                    "event__old_time",
                ),
                ConversionItem(
                    "result__extensions__" + VIDEO_EXTENSION_TIME_TO,
                    "event__new_time",
                ),
                ConversionItem(
                    "context__extensions__" + VIDEO_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )
