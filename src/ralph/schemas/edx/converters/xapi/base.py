"""Base xAPI Converter"""

from ralph.schemas.edx.converters.base import BaseConverter, GetFromField

from .constants import (
    VERSION,
    XAPI_EXTENSION_ACCEPT_LANGUAGE,
    XAPI_EXTENSION_AGENT,
    XAPI_EXTENSION_COURSE_ID,
    XAPI_EXTENSION_COURSE_USER_TAGS,
    XAPI_EXTENSION_HOST,
    XAPI_EXTENSION_IP,
    XAPI_EXTENSION_ORG_ID,
    XAPI_EXTENSION_PATH,
)


class BaseXapiConverter(BaseConverter):
    """Base xAPI Converter"""

    def __init__(self, platform):
        """Initialize BaseXapiConverter"""
        self.platform = platform
        super().__init__()

    def get_conversion_dictionary(self):
        """Returns a conversion dictionary used for conversion."""
        return {
            "actor": self.actor,
            "context": self.context,
            "object": self.object,
            "verb": self.verb,
            "version": VERSION,
            "timestamp": GetFromField("time"),
        }

    @property
    def actor(self):
        """Get statement actor from event (required)"""
        return {
            "account": {
                "name": GetFromField(
                    "context>user_id",
                    lambda user_id: str(user_id) if user_id else "student",
                ),
                "homePage": self.platform,
            },
            "objectType": "Agent",
        }

    @property
    def context(self):
        """Get statement context from event"""
        return {
            "platform": self.platform,
            "extensions": {
                XAPI_EXTENSION_ACCEPT_LANGUAGE: GetFromField("accept_language"),
                XAPI_EXTENSION_AGENT: GetFromField("agent"),
                XAPI_EXTENSION_COURSE_ID: GetFromField("context>course_id"),
                XAPI_EXTENSION_COURSE_USER_TAGS: GetFromField(
                    "context>course_user_tags"
                ),
                XAPI_EXTENSION_HOST: GetFromField("host"),
                XAPI_EXTENSION_IP: GetFromField("ip"),
                XAPI_EXTENSION_ORG_ID: GetFromField("context>org_id"),
                XAPI_EXTENSION_PATH: GetFromField("context>path"),
            },
        }

    @property
    def object(self):
        """Get statement object from event (required)"""
        raise NotImplementedError(
            f"{self.__class__.__name__} class should implement the object property"
        )

    @property
    def verb(self):
        """Get statement verb from event (required)"""
        raise NotImplementedError(
            f"{self.__class__.__name__} class should implement the verb property"
        )
