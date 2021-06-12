"""Problem interaction event xAPI Converter"""

from ralph.models.converter import ConversionItem
from ralph.models.edx.problem import DemandhintDisplayed
from ralph.models.xapi.problem.constants import (
    EXTENSION_SUPPLEMENTAL_INFO_ID,
    EXTENSION_TOTAL_ITEMS_ID,
)
from ralph.models.xapi.problem.statements import InteractionInteracted

from .base import BaseXapiConverter


class DemandhintDisplayedToInteractionInteracted(BaseXapiConverter):
    """Converts an `edx.problem.hint.demandhint_displayed` event to xAPI.

    Example Statement: John interacted with the question interaction.
    """

    __src__ = DemandhintDisplayed
    __dest__ = InteractionInteracted

    def _get_conversion_items(self):
        """Returns a set of ConversionItems used for conversion."""

        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "object__id",
                    "context__module__usage_key",
                    lambda usage_key: f"{self.home_page}/{usage_key}",
                ),
                ConversionItem(
                    "object__definition__extensions__" + EXTENSION_SUPPLEMENTAL_INFO_ID,
                    "event__hint_index",
                ),
                ConversionItem(
                    "object__definition__extensions__" + EXTENSION_TOTAL_ITEMS_ID,
                    "event__hint_len",
                ),
                ConversionItem("result__response", "event__hint_text"),
            }
        )
