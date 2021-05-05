"""PageViewed xAPI event definition"""

from .base import BaseXapiModel
from .fields.objects import PageObjectField
from .fields.verbs import TerminatedVerbField


class PageTerminated(BaseXapiModel):
    """Represents a page terminated xAPI statement.

    Example: John terminated the https://www.fun-mooc.fr/ page.

    Attributes:
       object (PageObjectField): See PageObjectField.
       verb (PageTerminatedVerbField): See PageTerminatedVerbField.
    """

    object: PageObjectField
    verb: TerminatedVerbField = TerminatedVerbField()
