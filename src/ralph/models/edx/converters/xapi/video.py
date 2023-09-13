"""Video event xAPI Converter."""

from ralph.models.converter import ConversionItem
from ralph.models.edx.video.statements import (
    UILoadVideo,
    UIPauseVideo,
    UIPlayVideo,
    UISeekVideo,
    UIStopVideo,
)
from ralph.models.xapi.concepts.constants.video import (
    CONTEXT_EXTENSION_LENGTH,
    CONTEXT_EXTENSION_SESSION_ID,
    CONTEXT_EXTENSION_USER_AGENT,
    RESULT_EXTENSION_PROGRESS,
    RESULT_EXTENSION_TIME,
    RESULT_EXTENSION_TIME_FROM,
    RESULT_EXTENSION_TIME_TO,
)
from ralph.models.xapi.constants import LANG_EN_US_DISPLAY
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
        """Return a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "object__definition__name",
                    "event__id",
                    lambda id: {LANG_EN_US_DISPLAY: id},
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
                    "context__contextActivities__category",
                    None,
                    lambda _: [{"id": "https://w3id.org/xapi/video"}],
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UILoadVideoToVideoInitialized(VideoBaseXapiConverter):
    """Convert a common edX `load_video` event to xAPI."""

    __src__ = UILoadVideo
    __dest__ = VideoInitialized

    def _get_conversion_items(self):
        """Return a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_LENGTH,
                    None,
                    # Set the video length to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `load_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_SESSION_ID,
                    "session",
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_USER_AGENT, "agent"
                ),
            },
        )


class UIPlayVideoToVideoPlayed(VideoBaseXapiConverter):
    """Convert a common edX `play_video` event to xAPI."""

    __src__ = UIPlayVideo
    __dest__ = VideoPlayed

    def _get_conversion_items(self):
        """Return a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + RESULT_EXTENSION_TIME,
                    "event__currentTime",
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UIPauseVideoToVideoPaused(VideoBaseXapiConverter):
    """Convert a common edX `pause_video` event to xAPI."""

    __src__ = UIPauseVideo
    __dest__ = VideoPaused

    def _get_conversion_items(self):
        """Return a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + RESULT_EXTENSION_TIME,
                    "event__currentTime",
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_LENGTH,
                    None,
                    # Set the video length to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `pause_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UIStopVideoToVideoTerminated(VideoBaseXapiConverter):
    """Convert a common edX `stop_video` event to xAPI."""

    __src__ = UIStopVideo
    __dest__ = VideoTerminated

    def _get_conversion_items(self):
        """Return a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + RESULT_EXTENSION_TIME,
                    "event__currentTime",
                ),
                ConversionItem(
                    "result__extensions__" + RESULT_EXTENSION_PROGRESS,
                    None,
                    # Set the video progress to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `stop_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_LENGTH,
                    None,
                    # Set the video length to null by default.
                    # This information is mandatory in the xAPI template
                    # and does not exist in the edX `stop_video` event model.
                    lambda _: 0.0,
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )


class UISeekVideoToVideoSeeked(VideoBaseXapiConverter):
    """Convert a common edX `seek_video` event to xAPI."""

    __src__ = UISeekVideo
    __dest__ = VideoSeeked

    def _get_conversion_items(self):
        """Return a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "result__extensions__" + RESULT_EXTENSION_TIME_FROM,
                    "event__old_time",
                ),
                ConversionItem(
                    "result__extensions__" + RESULT_EXTENSION_TIME_TO,
                    "event__new_time",
                ),
                ConversionItem(
                    "context__extensions__" + CONTEXT_EXTENSION_SESSION_ID,
                    "session",
                ),
            },
        )
