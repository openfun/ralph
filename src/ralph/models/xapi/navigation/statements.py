"""Navigation xAPI event definitions."""

from ...selector import selector
from ..base import BaseXapiModel
from ..fields.verbs import TerminatedVerbField, ViewedVerbField
from .fields.objects import PageObjectField


class PageViewed(BaseXapiModel):
    """Pydantic model for page viewed statement.

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
    """Pydantic model for page terminated statement.

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
