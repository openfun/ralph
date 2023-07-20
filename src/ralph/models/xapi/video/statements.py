"""Video xAPI event definitions."""

from ...selector import selector
from ..base.statements import BaseXapiStatement
from ..concepts.activity_types.video import VideoActivity
from ..concepts.verbs.scorm_profile import (
    CompletedVerb,
    InitializedVerb,
    InteractedVerb,
    TerminatedVerb,
)
from ..concepts.verbs.video import PausedVerb, PlayedVerb, SeekedVerb
from .contexts import (
    VideoCompletedContext,
    VideoEnableClosedCaptioningContext,
    VideoInitializedContext,
    VideoPausedContext,
    VideoPlayedContext,
    VideoScreenChangeInteractionContext,
    VideoSeekedContext,
    VideoTerminatedContext,
    VideoVolumeChangeInteractionContext,
)
from .results import (
    VideoCompletedResult,
    VideoEnableClosedCaptioningResult,
    VideoPausedResult,
    VideoPlayedResult,
    VideoScreenChangeInteractionResult,
    VideoSeekedResult,
    VideoTerminatedResult,
    VideoVolumeChangeInteractionResult,
)


class BaseVideoStatement(BaseXapiStatement):
    """Pydantic model for video core statements.

    Attributes:
        object (dict): See VideoActivity.
    """

    object: VideoActivity


class VideoInitialized(BaseVideoStatement):
    """Pydantic model for video initialized statement.

    Example: A video has been fully initialized.

    Attributes:
        verb (dict): See InitializedVerb.
        context (dict): See VideoInitializedContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/initialized",
    )

    verb: InitializedVerb = InitializedVerb()
    context: VideoInitializedContext


class VideoPlayed(BaseVideoStatement):
    """Pydantic model for video played statement.

    Example: John played the video or clicked the play button.

    Attributes:
        verb (dict): See PlayedVerb.
        result (dict): See VideoPlayedResult.
        context (dict): See VideoPlayedContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="https://w3id.org/xapi/video/verbs/played",
    )

    verb: PlayedVerb = PlayedVerb()
    result: VideoPlayedResult
    context: VideoPlayedContext


class VideoPaused(BaseVideoStatement):
    """Pydantic model for video paused statement.

    Example: John paused the video or clicked the pause button.

    Attributes:
        verb (dict): See PausedVerb.
        result (dict): See VideoPausedResult.
        context (dict): See VideoPausedContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="https://w3id.org/xapi/video/verbs/paused",
    )

    verb: PausedVerb = PausedVerb()
    result: VideoPausedResult
    context: VideoPausedContext


class VideoSeeked(BaseVideoStatement):
    """Pydantic model for video seeked statement.

    Example: John moved the progress bar forward or backward to a specific time in the
        video.

    Attributes:
        verb (dict): See SeekedVerb.
        result (dict): See VideoSeekedResult.
        context (dict): See VideoSeekedContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="https://w3id.org/xapi/video/verbs/seeked",
    )

    verb: SeekedVerb = SeekedVerb()
    result: VideoSeekedResult
    context: VideoSeekedContext


class VideoCompleted(BaseVideoStatement):
    """Pydantic model for video completed statement.

    Example: John completed a video by watching major parts of the video at least once.

    Attributes:
        verb (dict): See CompletedVerb.
        result (dict): See VideoCompletedResult.
        context (dict): See VideoCompletedContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/completed",
    )

    verb: CompletedVerb = CompletedVerb()
    result: VideoCompletedResult
    context: VideoCompletedContext


class VideoTerminated(BaseVideoStatement):
    """Pydantic model for video terminated statement.

    Example: John ended a video (quit the player).

    Attributes:
        verb (dict): See TerminatedVerb.
        result (dict): See VideoTerminatedResult.
        context (dict): See VideoTerminatedContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/terminated",
    )

    verb: TerminatedVerb = TerminatedVerb()
    result: VideoTerminatedResult
    context: VideoTerminatedContext


class VideoEnableClosedCaptioning(BaseVideoStatement):
    """Pydantic model for video enable closed captioning statement.

    Example: John interacted with the player to enable closed captioning.

    Attributes:
        verb (dict): See InteractedVerb.
        result (dict): See VideoEnableClosedCaptioningResult.
        context (dict): See VideoEnableClosedCaptioningContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/interacted",
    )

    verb: InteractedVerb = InteractedVerb()
    result: VideoEnableClosedCaptioningResult
    context: VideoEnableClosedCaptioningContext


class VideoVolumeChangeInteraction(BaseVideoStatement):
    """Pydantic model for video volume change interaction statement.

    Example: John interacted with the player to change the volume.

    Attributes :
        verb (dict): See InteractedVerb.
        result (dict): See VideoVolumeChangeInteractionResult.
        context (dict): See VideoVolumeChangeInteractionContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/interacted",
    )

    verb: InteractedVerb = InteractedVerb()
    result: VideoVolumeChangeInteractionResult
    context: VideoVolumeChangeInteractionContext


class VideoScreenChangeInteraction(BaseVideoStatement):
    """Pydantic model for video screen change interaction statement.

    Example: John interacted with the player to activate or deactivate full screen.

    Attributes:
        verb (dict): See InteractedVerb.
        result (dict): See VideoScreenChangeInteractionResult.
        context (dict): See VideoScreenChangeInteractionContext.
    """

    __selector__ = selector(
        object__definition__type="https://w3id.org/xapi/video/activity-type/video",
        verb__id="http://adlnet.gov/expapi/verbs/interacted",
    )

    verb: InteractedVerb = InteractedVerb()
    result: VideoScreenChangeInteractionResult
    context: VideoScreenChangeInteractionContext
