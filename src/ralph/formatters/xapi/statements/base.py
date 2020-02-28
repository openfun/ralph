"""
Ralph xAPI formatter base statements.
"""
import json
import logging

from ralph.settings import LMS_PLATFORM_URI

logger = logging.getLogger(__name__)


class Base:
    """Base xAPI statement formatter"""

    def __init__(self, event):
        """Instantiate base xAPI statement"""
        self._event = event

    def __dict__(self):
        """Base statement dictionnary"""
        return {
            "actor": self.actor,
            "context": self.context,
            "object": self.object,
            "result": self.result,
            "verb": self.verb,
            "timestamp": self.timestamp,
        }

    def __str__(self):
        """Return JSON string representation of the statement"""
        return self.json()

    def json(self):
        """Return JSON serialized statement"""
        return json.dumps(self.__dict__())

    @property
    def actor(self):
        """Get statement actor from event (required)"""
        return {
            "objectType": "Agent",
            "account": {"name": self._event.username, "homePage": LMS_PLATFORM_URI},
        }

    @property
    def context(self):
        """Get statement context from event"""
        return {"platform": LMS_PLATFORM_URI}

    @property
    def object(self):
        """Get statement object from event (required)"""
        raise NotImplementedError(
            f"{self.__class__.__name__} xAPI statement class should implement the object property"
        )

    @property
    def result(self):
        """Get statement result from event"""
        return None

    @property
    def verb(self):
        """Get statement verb from event (required)"""
        raise NotImplementedError(
            f"{self.__class__.__name__} xAPI statement class should implement the verb property"
        )

    @property
    def timestamp(self):
        """Get statement time stamp.

        Note that it is supposed to be a datetime instance.
        """
        return self._event.time.isoformat()
