"""Server event xAPI Converter"""

from ralph.models.xapi.constants import (
    XAPI_EXTENSION_ACCEPT_LANGUAGE,
    XAPI_EXTENSION_AGENT,
    XAPI_EXTENSION_COURSE_ID,
    XAPI_EXTENSION_COURSE_USER_TAGS,
    XAPI_EXTENSION_HOST,
    XAPI_EXTENSION_IP,
    XAPI_EXTENSION_ORG_ID,
    XAPI_EXTENSION_PATH,
)
from ralph.models.xapi.page_viewed import PageViewed

from .base import BaseXapiConverter


class ServerEventToXapi(BaseXapiConverter):
    """Converts a common edX server event to xAPI.

    Example Statement: John viewed https://www.fun-mooc.fr/ Web page.

    WARNING: Duplicate xAPI values:
        - object.id == context.extensions.XAPI_EXTENSION_PATH.

    WARNING: The converter does not include the following edX fields:
        - username: As it is similar to the `context.user_id` field.
        - referer: As it may contain sensitive data.
        - event: As it may contain sensitive data.
        - event_source: As it is replaced by xAPIs `object.definition`.

    WARNING: The converter may not include the following edX fields:
        - ip: When `ip` is an empty string.
        - agent: When `agent` is an empty string.
        - accept_language: When `accept_language` is an empty string.
        - context.course_user_tags: When `course_user_tags` is an empty dictionary.
        - context.org_id: When `org_id` is an empty string.
        - context.course_id: When `course_id` is an empty string.
    """

    __model__ = PageViewed

    def get_conversion_set(self):
        """Returns a conversion set used for conversion."""

        return {
            ("actor__account__homePage", lambda: self.platform),
            (
                "actor__account__name",
                "context__user_id",
                lambda user_id: user_id if user_id else "anonymous",
            ),
            (
                "context__extensions__" + XAPI_EXTENSION_ACCEPT_LANGUAGE,
                "accept_language",
            ),
            ("context__extensions__" + XAPI_EXTENSION_AGENT, "agent"),
            ("context__extensions__" + XAPI_EXTENSION_COURSE_ID, "context__course_id"),
            (
                "context__extensions__" + XAPI_EXTENSION_COURSE_USER_TAGS,
                "context__course_user_tags",
                lambda tags: {k: v for k, v in tags.items() if k and v}
                if tags
                else None,
            ),
            ("context__extensions__" + XAPI_EXTENSION_HOST, "host"),
            ("context__extensions__" + XAPI_EXTENSION_IP, "ip"),
            ("context__extensions__" + XAPI_EXTENSION_ORG_ID, "context__org_id"),
            ("context__extensions__" + XAPI_EXTENSION_PATH, "context__path"),
            ("object__id", "event_type", lambda event_type: self.platform + event_type),
            ("timestamp", "time"),
        }
