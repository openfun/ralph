"""xAPI pydantic models"""

# flake8: noqa

from .video.statements import (
    VideoCompleted,
    VideoInitialized,
    VideoInteracted,
    VideoPaused,
    VideoPlayed,
    VideoSeeked,
    VideoTerminated,
)

from .navigation.statements import PageTerminated, PageViewed
