"""Navigation xAPI event definitions"""

from ..base import BaseXapiModel
from ..fields.verbs import TerminatedVerbField, ViewedVerbField
from .fields.objects import PageObjectField


class PageViewed(BaseXapiModel):
    """Represents a page viewed xAPI statement.

    Example: John viewed the https://www.fun-mooc.fr/ page.

    Attributes:
       object (PageObjectField): See PageObjectField.
       verb (PageViewedVerbField): See PageViewedVerbField.
    """

    object: PageObjectField
    verb: ViewedVerbField = ViewedVerbField()


class PageTerminated(BaseXapiModel):
    """Represents a page terminated xAPI statement.

    Example: John terminated the https://www.fun-mooc.fr/ page.

    Attributes:
       object (PageObjectField): See PageObjectField.
       verb (PageTerminatedVerbField): See PageTerminatedVerbField.
    """

    object: PageObjectField
    verb: TerminatedVerbField = TerminatedVerbField()
