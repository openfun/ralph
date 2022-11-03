"""Video xAPI event definitions"""

from typing import Optional

from ...selector import selector
from ..base import BaseXapiModel
from .fields.contexts import (
    VideoCompletedContextField,
    VideoEnableClosedCaptioningContextField,
    VideoInitializedContextField,
    VideoPausedContextField,
    VideoPlayedContextField,
    VideoScreenChangeInteractionContextField,
    VideoSeekedContextField,
    VideoTerminatedContextField,
    VideoVolumeChangeInteractionContextField,
)
from .fields.objects import VideoObjectField
from .fields.results import (
    VideoCompletedResultField,
    VideoEnableClosedCaptioningResultField,
    VideoPausedResultField,
    VideoPlayedResultField,
    VideoScreenChangeInteractionResultField,
    VideoSeekedResultField,
    VideoTerminatedResultField,
    VideoVolumeChangeInteractionResultField,
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
    """Pydantic model for video core statements.

    Attributes:
        object (dict): See VideoObjectField.
    """

    object: VideoObjectField


class VideoInitialized(BaseVideoStatement):
    """Pydantic model for video initialized statement.

    Example: A video has been fully initialized.

    Attributes:
        verb (dict): See VideoInitializedVerbField.
        context (dict): See VideoInitializedContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/initialized",
    )

    verb: VideoInitializedVerbField = VideoInitializedVerbField()
    context: VideoInitializedContextField


class VideoPlayed(BaseVideoStatement):
    """Pydantic model for video played statement.

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

    verb: VideoPlayedVerbField = VideoPlayedVerbField()
    result: VideoPlayedResultField
    context: Optional[VideoPlayedContextField]


class VideoPaused(BaseVideoStatement):
    """Pydantic model for video paused statement.

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

    verb: VideoPausedVerbField = VideoPausedVerbField()
    result: VideoPausedResultField
    context: VideoPausedContextField


class VideoSeeked(BaseVideoStatement):
    """Pydantic model for video seeked statement.

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

    verb: VideoSeekedVerbField = VideoSeekedVerbField()
    result: VideoSeekedResultField
    context: Optional[VideoSeekedContextField]


class VideoCompleted(BaseVideoStatement):
    """Pydantic model for video completed statement.

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

    verb: VideoCompletedVerbField = VideoCompletedVerbField()
    result: VideoCompletedResultField
    context: VideoCompletedContextField


class VideoTerminated(BaseVideoStatement):
    """Pydantic model for video terminated statement.

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

    verb: VideoTerminatedVerbField = VideoTerminatedVerbField()
    result: VideoTerminatedResultField
    context: VideoTerminatedContextField


class VideoEnableClosedCaptioning(BaseVideoStatement):
    """Represents a video enable closed captioning xAPI statement.

    Example: John interacted with the player to enable closed captioning.

    Attributes:
        verb (dict): See VideoInteractedVerbField.
        result (dict): See VideoEnableClosedCaptioningResultField.
        context (dict): See VideoEnableClosedCaptioningContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/interacted",
    )

    verb: VideoInteractedVerbField = VideoInteractedVerbField()
    result: VideoEnableClosedCaptioningResultField
    context: VideoEnableClosedCaptioningContextField


class VideoVolumeChangeInteraction(BaseVideoStatement):
    """Represents a video volume change interaction xAPI statement.

    Example: John interacted with the player to change the volume.

    Attributes:
        verb (dict): See VideoInteractedVerbField.
        result (dict): See VideoVolumeChangeInteractionResultField.
        context (dict): See VideoVolumeChangeInteractionContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/interacted",
    )

    verb: VideoInteractedVerbField = VideoInteractedVerbField()
    result: VideoVolumeChangeInteractionResultField
    context: VideoVolumeChangeInteractionContextField


class VideoScreenChangeInteraction(BaseVideoStatement):
    """Represents a video screen change interaction xAPI statement.

    Example: John interacted with the player to activate or deactivate full screen.

    Attributes:
        verb (dict): See VideoInteractedVerbField.
        result (dict): See VideoScreenChangeInteractionResultField.
        context (dict): See VideoScreenChangeInteractionContextField.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/interacted",
    )

    verb: VideoInteractedVerbField = VideoInteractedVerbField()
    result: VideoScreenChangeInteractionResultField
    context: VideoScreenChangeInteractionContextField
