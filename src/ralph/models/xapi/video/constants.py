"""Constants for xAPI video specifications."""

from typing import Literal

# xAPI video extensions
VIDEO_EXTENSION_CC_SUBTITLE_LANG = (
    "https://w3id.org/xapi/video/extensions/cc-subtitle-lang"
)
VIDEO_EXTENSION_CC_ENABLED = "https://w3id.org/xapi/video/extensions/cc-enabled"
VIDEO_EXTENSION_COMPLETION_THRESHOLD = (
    "https://w3id.org/xapi/video/extensions/completion-threshold"
)
VIDEO_EXTENSION_FRAME_RATE = "https://w3id.org/xapi/video/extensions/frame-rate"
VIDEO_EXTENSION_FULL_SCREEN = "https://w3id.org/xapi/video/extensions/full-screen"
VIDEO_EXTENSION_LENGTH = "https://w3id.org/xapi/video/extensions/length"
VIDEO_EXTENSION_PLAYED_SEGMENTS = (
    "https://w3id.org/xapi/video/extensions/played-segments"
)
VIDEO_EXTENSION_PROGRESS = "https://w3id.org/xapi/video/extensions/progress"
VIDEO_EXTENSION_QUALITY = "https://w3id.org/xapi/video/extensions/quality"

VIDEO_EXTENSION_SCREEN_SIZE = "https://w3id.org/xapi/video/extensions/screen-size"
VIDEO_EXTENSION_SESSION_ID = "https://w3id.org/xapi/video/extensions/session-id"
VIDEO_EXTENSION_SPEED = "https://w3id.org/xapi/video/extensions/speed"
VIDEO_EXTENSION_TIME = "https://w3id.org/xapi/video/extensions/time"
VIDEO_EXTENSION_TIME_FROM = "https://w3id.org/xapi/video/extensions/time-from"
VIDEO_EXTENSION_TIME_TO = "https://w3id.org/xapi/video/extensions/time-to"
VIDEO_EXTENSION_TRACK = "https://w3id.org/xapi/video/extensions/track"
VIDEO_EXTENSION_USER_AGENT = "https://w3id.org/xapi/video/extensions/user-agent"
VIDEO_EXTENSION_VIDEO_PLAYBACK_SIZE = (
    "https://w3id.org/xapi/video/extensions/video-playback-size"
)
VIDEO_EXTENSION_VOLUME = "https://w3id.org/xapi/video/extensions/volume"


# xAPI video object definition type
VIDEO_OBJECT_DEFINITION_TYPE = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video/activity-type/video"
]

# Video context category
VIDEO_CONTEXT_CATEGORY = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video"
]

# xAPI video verbs
VERB_VIDEO_PAUSED_ID = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video/verbs/paused"
]
VERB_VIDEO_PLAYED_ID = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video/verbs/played"
]
VERB_VIDEO_SEEKED_ID = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video/verbs/seeked"
]
