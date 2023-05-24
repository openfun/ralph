"""Base xAPI Converter."""

from typing import Set
from uuid import UUID, uuid5

from ralph.exceptions import ConfigurationException
from ralph.models.converter import BaseConversionSet, ConversionItem


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
        """Initialize BaseXapiConverter."""
        self.platform_url = platform_url
        try:
            self.uuid_namespace = UUID(uuid_namespace)
        except (TypeError, ValueError, AttributeError) as err:
            raise ConfigurationException("Invalid UUID namespace") from err
        super().__init__()

    def _get_conversion_items(self) -> Set[ConversionItem]:
        """Return a set of ConversionItems used for conversion."""
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
                lambda user_id: str(user_id) if user_id else "anonymous",
            ),
            ConversionItem("timestamp", "time"),
        }
