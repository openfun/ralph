"""Server event xAPI Converter"""

from ralph.schemas.edx.converters.base import GetFromField
from ralph.schemas.edx.server_event import ServerEventSchema

from .base import BaseXapiConverter
from .constants import (
    PAGE,
    VIEWED,
    XAPI_ACTIVITY_PAGE,
    XAPI_EXTENSION_REQUEST,
    XAPI_VERB_VIEWED,
)


class ServerEventToXapi(BaseXapiConverter):
    """Converts a common edX server event to xAPI
    See ServerEventSchema for info about the edX server event
    Example Statement: John viewed https://www.fun-mooc.fr/ Web page
    """

    _schema = ServerEventSchema()

    @property
    def object(self):
        """Get statement object from event (required)"""
        return {
            "id": GetFromField(
                "event_type", lambda event_type: self.platform + event_type
            ),
            "definition": {
                "type": XAPI_ACTIVITY_PAGE,
                "name": {"en": PAGE},
            },
            "objectType": "Activity",
        }

    @property
    def verb(self):
        """Get statement verb from event (required)"""
        return {"id": XAPI_VERB_VIEWED, "display": {"en": VIEWED}}

    @property
    def context(self):
        context = super().context
        context["extensions"][XAPI_EXTENSION_REQUEST] = GetFromField("event")
        return context
