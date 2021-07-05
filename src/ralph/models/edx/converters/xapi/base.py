"""Base xAPI Converter"""

import re
from uuid import UUID, uuid5

from ralph.exceptions import ConfigurationException
from ralph.models.converter import BaseConversionSet, ConversionItem
from ralph.models.xapi.constants import (
    EXTENSION_COURSE_ID,
    EXTENSION_MODULE_ID,
    EXTENSION_SCHOOL_ID,
)


class BaseXapiConverter(BaseConversionSet):
    """Base xAPI Converter.

    WARNING: The converter may not include the following edX fields:
    - context.org_id: When `org_id` is an empty string.
    - context.course_id: When `course_id` is an empty string.

    WARNING: The converter should not include the following edX fields as they may
    contain sensitive data: `username`, `referer`, `event`, `event_source`, `ip`,
    `agent`, `accept_language:`, `context.course_user_tags`.
    """

    def __init__(self, uuid_namespace: str, platform_url: str):
        """Initializes BaseXapiConverter."""

        self.platform_url = platform_url
        try:
            self.uuid_namespace = UUID(uuid_namespace)
        except (TypeError, ValueError, AttributeError) as err:
            raise ConfigurationException("Invalid UUID namespace") from err
        super().__init__()

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        return {
            ConversionItem(
                "id",
                None,
                lambda event_str: str(uuid5(self.uuid_namespace, event_str)),
                True,
            ),
            ConversionItem(
                "actor__account__homePage", transformers=lambda _: self.platform_url
            ),
            ConversionItem(
                "actor__account__name",
                "context__user_id",
                lambda user_id: user_id if user_id else "anonymous",
            ),
            ConversionItem(
                "object__definition__extensions__" + EXTENSION_SCHOOL_ID,
                "context__org_id",
            ),
            ConversionItem(
                "object__definition__extensions__" + EXTENSION_COURSE_ID,
                "context__course_id",
                (self.parse_course_id, lambda x: x["course"]),
            ),
            ConversionItem(
                "object__definition__extensions__" + EXTENSION_MODULE_ID,
                "context__course_id",
                (self.parse_course_id, lambda x: x["module"]),
            ),
            ConversionItem("timestamp", "time"),
        }

    @staticmethod
    def parse_course_id(course_id: str):
        """Returns a dictionary with `course` and `module` of edX event's `context.course_id`."""

        match = re.match(r"^course-v1:.+\+(.+)\+(.+)$", course_id)
        if not match:
            return {"course": None, "module": None}
        return {"course": match.group(1), "module": match.group(2)}
