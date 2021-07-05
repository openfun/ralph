"""Constants for xAPI specifications"""

from typing import Literal

# Languages
LANG_EN_DISPLAY = Literal["en"]  # pylint:disable=invalid-name
LANG_EN_US_DISPLAY = Literal["en-US"]  # pylint:disable=invalid-name

# xAPI activities
ACTIVITY_PAGE_DISPLAY = Literal["page"]  # pylint:disable=invalid-name
ACTIVITY_PAGE_ID = Literal[  # pylint:disable=invalid-name
    "http://activitystrea.ms/schema/1.0/page"
]

# xAPI verbs
VERB_COMPLETED_DISPLAY = Literal["completed"]  # pylint:disable=invalid-name
VERB_INITIALIZED_DISPLAY = Literal["initialized"]  # pylint:disable=invalid-name
VERB_INTERACTED_DISPLAY = Literal["interacted"]  # pylint:disable=invalid-name
VERB_PAUSED_DISPLAY = Literal["paused"]  # pylint:disable=invalid-name
VERB_PLAYED_DISPLAY = Literal["played"]  # pylint:disable=invalid-name
VERB_SEEKED_DISPLAY = Literal["seeked"]  # pylint:disable=invalid-name
VERB_TERMINATED_DISPLAY = Literal["terminated"]  # pylint:disable=invalid-name
VERB_VIEWED_DISPLAY = Literal["viewed"]  # pylint:disable=invalid-name

# xAPI verbs IDs
VERB_COMPLETED_ID = Literal[  # pylint:disable=invalid-name
    "http://adlnet.gov/expapi/verbs/completed"
]
VERB_INITIALIZED_ID = Literal[  # pylint:disable=invalid-name
    "http://adlnet.gov/expapi/verbs/initialized"
]
VERB_INTERACTED_ID = Literal[  # pylint:disable=invalid-name
    "http://adlnet.gov/expapi/verbs/interacted"
]
VERB_TERMINATED_ID = Literal[  # pylint:disable=invalid-name
    "http://adlnet.gov/expapi/verbs/terminated"
]
VERB_VIEWED_ID = Literal[  # pylint:disable=invalid-name
    "http://id.tincanapi.com/verb/viewed"
]
# xAPI extensions
EXTENSION_COURSE_ID = "http://adlnet.gov/expapi/activities/course"
EXTENSION_MODULE_ID = "http://adlnet.gov/expapi/activities/module"
EXTENSION_SCHOOL_ID = "https://w3id.org/xapi/acrossx/extensions/school"
