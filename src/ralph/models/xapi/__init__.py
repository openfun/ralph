"""xAPI pydantic models."""

# flake8: noqa

from .lms.statements import (
    LMSAccessedFile,
    LMSAccessedPage,
    LMSDownloadedAudio,
    LMSDownloadedDocument,
    LMSDownloadedFile,
    LMSDownloadedVideo,
    LMSRegisteredCourse,
    LMSUnregisteredCourse,
    LMSUploadedAudio,
    LMSUploadedDocument,
    LMSUploadedFile,
    LMSUploadedVideo,
)
from .navigation.statements import PageTerminated, PageViewed
from .video.statements import (
    VideoCompleted,
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
