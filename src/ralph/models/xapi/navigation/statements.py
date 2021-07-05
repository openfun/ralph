"""Navigation xAPI event definitions"""

from ...selector import selector
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

    __selector__ = selector(
        object__definition__type="http://activitystrea.ms/schema/1.0/page",
        verb__id="http://id.tincanapi.com/verb/viewed",
    )

    object: PageObjectField
    verb: ViewedVerbField = ViewedVerbField()


class PageTerminated(BaseXapiModel):
    """Represents a page terminated xAPI statement.

    Example: John terminated the https://www.fun-mooc.fr/ page.

    Attributes:
       object (PageObjectField): See PageObjectField.
       verb (PageTerminatedVerbField): See PageTerminatedVerbField.
    """

    __selector__ = selector(
        object__definition__type="http://activitystrea.ms/schema/1.0/page",
        verb__id="http://adlnet.gov/expapi/verbs/terminated",
    )

    object: PageObjectField
    verb: TerminatedVerbField = TerminatedVerbField()
