"""Video xAPI event definitions"""

from ...selector import selector
from ..base import BaseXapiModel
from .fields.contexts import (
    VideoCompletedContextField,
    VideoInitializedContextField,
    VideoInteractedContextField,
    VideoPausedContextField,
    VideoPlayedContextField,
    VideoSeekedContextField,
    VideoTerminatedContextField,
)
from .fields.objects import VideoObjectField
from .fields.results import (
    VideoCompletedResultField,
    VideoInteractedResultField,
    VideoPausedResultField,
    VideoPlayedResultField,
    VideoSeekedResultField,
    VideoTerminatedResultField,
)
from .fields.verbs import (
    VideoCompletedVerbField,
    VideoInitializedVerbField,
    VideoInteractedVerbField,
    VideoPausedVerbField,
    VideoPlayedVerbField,
    VideoSeekedVerbField,
    VideoTerminatedVerbField,
)


class BaseVideoStatement(BaseXapiModel):
    """Base model for xAPI video statements.

    Attributes:
        object (dict): See VideoObjectField.
    """

    object: VideoObjectField


class VideoInitialized(BaseVideoStatement):
    """Represents a video initialized xAPI statement.

    Example: A video has been fully initialized.

    Attributes:
        verb (dict): See VideoInitializedVerbField.
        context (dict): See VideoInitializedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/initialized",
    )

    verb: VideoInitializedVerbField
    context: VideoInitializedContextField


class VideoPlayed(BaseVideoStatement):
    """Represents a video played xAPI statement.

    Example: John played the video or clicked the play button.

    Attributes:
        verb (dict): See VideoPlayedVerbField.
        result (dict): See VideoPlayedResultField.
        context (dict): See VideoPlayedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="https://w3id.org/xapi/video/verbs/played",
    )

    verb: VideoPlayedVerbField
    result: VideoPlayedResultField
    context: VideoPlayedContextField


class VideoPaused(BaseVideoStatement):
    """Represents a video paused xAPI statement.

    Example: John paused the video or clicked the pause button.

    Attributes:
        verb (dict): See VideoPausedVerbField.
        result (dict): See VideoPausedResultField.
        context (dict): See VideoPausedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="https://w3id.org/xapi/video/verbs/paused",
    )

    verb: VideoPausedVerbField
    result: VideoPausedResultField
    context: VideoPausedContextField


class VideoSeeked(BaseVideoStatement):
    """Represents a video seeked xAPI statement.

    Example: John moved the progress bar forward or backward to a specific time in the
        video.

    Attributes:
        verb (dict): See VideoSeekedVerbField.
        result (dict): See VideoSeekedResultField.
        context (dict): See VideoSeekedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="https://w3id.org/xapi/video/verbs/seeked",
    )

    verb: VideoSeekedVerbField
    result: VideoSeekedResultField
    context: VideoSeekedContextField


class VideoCompleted(BaseVideoStatement):
    """Represents a video completed xAPI statement.

    Example: John completed a video by watching major parts of the video at least once.

    Attributes:
        verb (dict): See VideoCompletedVerbField.
        result (dict): See VideoCompletedResultField.
        context (dict): See VideoCompletedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/completed",
    )

    verb: VideoCompletedVerbField
    result: VideoCompletedResultField
    context: VideoCompletedContextField


class VideoTerminated(BaseVideoStatement):
    """Represents a video terminated xAPI statement.

    Example: John ended a video (quit the player).

    Attributes:
        verb (dict): See VideoTerminatedVerbField.
        result (dict): See VideoTerminatedResultField.
        context (dict): See VideoTerminatedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/terminated",
    )

    verb: VideoTerminatedVerbField
    result: VideoTerminatedResultField
    context: VideoTerminatedContextField


class VideoInteracted(BaseVideoStatement):
    """Represents a video terminated xAPI statement.

    Example: John interacted with the player (except play, pause, seek). e.g. mute,
        unmute, change resolution, change player size, etc.

    Attributes:
        verb (dict): See VideoInteractedVerbField.
        result (dict): See VideoInteractedResultField.
        context (dict): See VideoInteractedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/interacted",
    )

    verb: VideoInteractedVerbField
    result: VideoInteractedResultField
    context: VideoInteractedContextField
