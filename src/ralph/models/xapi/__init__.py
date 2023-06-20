"""xAPI pydantic models."""

# flake8: noqa

from .navigation.statements import PageTerminated, PageViewed
from .video.statements import (
    VideoCompleted,
    VideoDownloaded,
    VideoEnableClosedCaptioning,
    VideoInitialized,
    VideoPaused,
    VideoPlayed,
    VideoScreenChangeInteraction,
    VideoSeeked,
    VideoTerminated,
    VideoVolumeChangeInteraction,
)
from .virtual_classroom.statements import (
    VirtualClassroomAnsweredPoll,
    VirtualClassroomInitialized,
    VirtualClassroomJoined,
    VirtualClassroomLeft,
    VirtualClassroomLoweredHand,
    VirtualClassroomMuted,
    VirtualClassroomPostedPublicMessage,
    VirtualClassroomRaisedHand,
    VirtualClassroomSharedScreen,
    VirtualClassroomStartedCamera,
    VirtualClassroomStartedPoll,
    VirtualClassroomStoppedCamera,
    VirtualClassroomTerminated,
    VirtualClassroomUnmuted,
    VirtualClassroomUnsharedScreen,
)
