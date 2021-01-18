"""Constants for xAPI specifications"""

# Languages
EN = "en"

# xAPI activities
XAPI_ACTIVITY_BOOK = "http://id.tincanapi.com/activitytype/book"
XAPI_ACTIVITY_PAGE = "http://activitystrea.ms/schema/1.0/page"
# XAPI_ACTIVITY_SOLUTION = "http://id.tincanapi.com/activitytype/solution"
XAPI_ACTIVITY_MODULE = "http://adlnet.gov/expapi/activities/module"

# xAPI verbs
# XAPI_VERB_ASKED = "http://adlnet.gov/expapi/verbs/asked"
XAPI_VERB_INITIALIZED = "http://adlnet.gov/expapi/verbs/initialized"
XAPI_VERB_INTERACTED = "http://adlnet.gov/expapi/verbs/interacted"
XAPI_VERB_TERMINATED = "http://adlnet.gov/expapi/verbs/terminated"
XAPI_VERB_VIEWED = "http://id.tincanapi.com/verb/viewed"

# xAPI extensions
XAPI_EXTENSION_ACCEPT_LANGUAGE = "https://www.edx.org/extension/accept_language"
XAPI_EXTENSION_AGENT = "https://www.edx.org/extension/agent"
XAPI_EXTENSION_COLLECTION_TYPE = "http://id.tincanapi.com/extension/collection-type"
XAPI_EXTENSION_COURSE_ID = "https://www.edx.org/extension/course_id"
XAPI_EXTENSION_COURSE_USER_TAGS = "https://www.edx.org/extension/course_user_tags"
XAPI_EXTENSION_DIRECTION = "https://www.edx.org/extension/textbook/direction"
XAPI_EXTENSION_ENDING_POSITION = "http://id.tincanapi.com/extension/ending-position"
XAPI_EXTENSION_HOST = "https://www.edx.org/extension/host"
XAPI_EXTENSION_IP = "https://www.edx.org/extension/ip"
XAPI_EXTENSION_ORG_ID = "https://www.edx.org/extension/org_id"
XAPI_EXTENSION_PATH = "https://www.edx.org/extension/path"
XAPI_EXTENSION_POSITION = "http://id.tincanapi.com/extension/position"
XAPI_EXTENSION_REQUEST = "https://www.edx.org/extension/request"
XAPI_EXTENSION_SESSION = "https://www.edx.org/extension/session"
XAPI_EXTENSION_STARTING_POSITION = "http://id.tincanapi.com/extension/starting-position"
XAPI_EXTENSION_THUMBNAIL_TITLE = (
    "https://www.edx.org/extension/textbook/thumbnail_title"
)
XAPI_EXTENSION_USER_ID = "https://www.edx.org/extension/user_id"
XAPI_EXTENSION_ZOOM_AMOUNT = "https://www.edx.org/extension/textbook/zoom/amount"

# Display Names
# ASKED = "asked"
BOOK = "book"
INITIALIZED = "initialized"
INTERACTED = "interacted"
MODULE = "module"
PAGE = "page"
# SOLUTION = "solution"
TERMINATED = "terminated"
VIEWED = "viewed"

# Other
VERSION = "1.0.3"
