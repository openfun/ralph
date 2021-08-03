"""Navigational event xAPI Converter"""

from ralph.models.converter import ConversionItem
from ralph.models.edx.navigational.statements import UIPageClose
from ralph.models.xapi.navigation.statements import PageTerminated

from .base import BaseXapiConverter


class UIPageCloseToPageTerminated(BaseXapiConverter):
    """Converts a common edX `page_close` event to xAPI.

    Example Statement: John terminated https://www.fun-mooc.fr/ page.

    WARNING: The converter does not use the `self.platform_url` in the `object__id`.
    """

    __src__ = UIPageClose
    __dest__ = PageTerminated

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union({ConversionItem("object__id", "page")})
