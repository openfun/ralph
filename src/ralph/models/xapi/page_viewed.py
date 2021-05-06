"""PageViewed xAPI event definition"""

from .base import BaseXapiModel
from .fields.object import PageObjectField
from .fields.verb import PageViewedVerbField


class PageViewed(BaseXapiModel):
    """Represents a page viewed xAPI statement.

    Example: John viewed the https://www.fun-mooc.fr/ page.

    Attributes:
       object (PageObjectField): See PageObjectField.
       verb (PageViewedVerbField): See PageViewedVerbField.
    """

    object: PageObjectField
    verb: PageViewedVerbField = PageViewedVerbField()
