"""Navigation xAPI event definitions."""

from ...selector import selector
from ..base.statements import BaseXapiStatement
from ..concepts.activity_types.activity_streams_vocabulary import PageActivity
from ..concepts.verbs.scorm_profile import TerminatedVerb
from ..concepts.verbs.tincan_vocabulary import ViewedVerb


class PageViewed(BaseXapiStatement):
    """Pydantic model for page viewed statement.

    Example: John viewed the https://www.fun-mooc.fr/ page.

    Attributes:
       object (dict): See PageActivity.
       verb (dict): See ViewedVerb.
    """

    __selector__ = selector(
        object__definition__type="http://activitystrea.ms/schema/1.0/page",
        verb__id="http://id.tincanapi.com/verb/viewed",
    )

    object: PageActivity
    verb: ViewedVerb = ViewedVerb()


class PageTerminated(BaseXapiStatement):
    """Pydantic model for page terminated statement.

    Example: John terminated the https://www.fun-mooc.fr/ page.

    Attributes:
       object (dict): See PageActivity.
       verb (dict): See TerminatedVerb.
    """

    __selector__ = selector(
        object__definition__type="http://activitystrea.ms/schema/1.0/page",
        verb__id="http://adlnet.gov/expapi/verbs/terminated",
    )

    object: PageActivity
    verb: TerminatedVerb = TerminatedVerb()
