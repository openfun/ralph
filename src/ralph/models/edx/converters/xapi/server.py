"""Server event xAPI Converter."""

from ralph.models.converter import ConversionItem
from ralph.models.edx.server import Server
from ralph.models.xapi.navigation.statements import PageViewed

from .base import BaseXapiConverter


class ServerEventToPageViewed(BaseXapiConverter):
    """Converts a common edX server event to xAPI.

    Example Statement: John viewed https://www.fun-mooc.fr/ page.
    """

    __src__ = Server
    __dest__ = PageViewed

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "object__id",
                    "event_type",
                    lambda event_type: self.platform_url + event_type,
                ),
            }
        )
