"""PageViewed xAPI event definition"""

from .base import BaseXapiModel
from .fields.object import PageObjectField
from .fields.verb import PageTerminatedVerbField


class PageTerminated(BaseXapiModel):
    """Represents a page terminated xAPI statement.

    Example: John terminated the https://www.fun-mooc.fr/ page.

    Attributes:
       object (PageObjectField): See PageObjectField.
       verb (PageTerminatedVerbField): See PageTerminatedVerbField.
    """

    object: PageObjectField
    verb: PageTerminatedVerbField = PageTerminatedVerbField()
