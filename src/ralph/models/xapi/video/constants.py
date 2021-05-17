"""Constants for xAPI video specifications"""

from typing import Literal

# xAPI video extensions
VIDEO_CONTEXT_EXTENSION_SESSION_ID = "https://w3id.org/xapi/video/extensions/session-id"
VIDEO_RESULT_EXTENSION_TIME = "https://w3id.org/xapi/video/extensions/time"


# xAPI video ID
VERB_VIDEO_PLAYED_ID = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video/verbs/played"
]

# xAPI video object definition type
VIDEO_OBJECT_DEFINITION_TYPE = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video/activity-type/video"
]

# Video context category
VIDEO_CONTEXT_CATEGORY = Literal[  # pylint:disable=invalid-name
    "https://w3id.org/xapi/video"
]
