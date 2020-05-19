"""
Ralph xAPI formatter problem-related statements.
"""
import json
import logging

from ralph.exceptions import IgnoredEvent
from .base import Base
from ..utils import activity_identifier, activity_name


logger = logging.getLogger(__name__)


class ProblemCheck(Base):
    """Problem check statement formatter"""

    def __init__(self, event):
        """Ignore browser events"""
        super().__init__(event)
        if self._event.event_source.lower() != "server":
            raise IgnoredEvent(
                f"{self.__class__.__name__} statement only consider server events, not {self._event.event_source}"
            )

    @property
    def object(self):
        """Get statement object from event (required)"""
        return {
            "objectType": "Activity",
            "id": activity_identifier(self._event),
            "definition": {
                # FIXME
                # Handle non-capa activity
                "type": "http://adlnet.gov/expapi/activities/interaction",
                "name": {"en-US": activity_name(self._event)},
                "description": {"en-US": "Problem check in an OpenEdx course"},
            },
        }

    @property
    def result(self):
        """Get statement result from event"""
        event = self._event.event
        return {
            "score": {
                "raw": event["grade"],
                "min": 0,
                "max": event["max_grade"],
                "scaled": float(event["grade"] / event["max_grade"]),
            },
            "success": event["success"] == "correct",
            # FIXME
            # this is silly
            "response": json.dumps(event["submission"]),
        }

    @property
    def verb(self):
        """Get statement verb from event (required)"""
        return {
            "id": "http://adlnet.gov/expapi/verbs/answered",
            "display": {"en-US": "answered"},
        }
