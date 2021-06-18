"""xAPI pydantic models"""

# flake8: noqa

from .navigation.statements import PageTerminated, PageViewed
from .video.statements import (
    VideoCompleted,
    VideoInitialized,
    VideoInteracted,
    VideoPaused,
    VideoPlayed,
    VideoSeeked,
    VideoTerminated,
)
