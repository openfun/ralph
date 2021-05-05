"""PageViewed xAPI event definition"""

from .base import BaseXapiModel
from .fields.objects import PageObjectField
from .fields.verbs import ViewedVerbField


class PageViewed(BaseXapiModel):
    """Represents a page viewed xAPI statement.

    Example: John viewed the https://www.fun-mooc.fr/ page.

    Attributes:
       object (PageObjectField): See PageObjectField.
       verb (PageViewedVerbField): See PageViewedVerbField.
    """

    object: PageObjectField
    verb: ViewedVerbField = ViewedVerbField()
