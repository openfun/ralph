"""Entrypoint to convert events to xAPI"""

import json
import logging
from enum import Enum

from .xapi.server_event_to_xapi import ServerEventToXapi

# converters module logger
logger = logging.getLogger(__name__)


class Converters(Enum):
    """Stores initialized xAPI converters"""

    SERVER = ServerEventToXapi


class XapiConverterSelector:
    """Select a matching xAPI converter to convert to xAPI format"""

    def __init__(self, platform):
        """Initialise XapiConverterSelector

        Args:
            platform (str): URL of the platform to which the event belongs

        """

        self.event = None
        self.converters = {
            converter: converter.value(platform) for converter in Converters
        }

    def convert(self, input_file):
        """Uses a matching xAPI converter to validate and return the converted event"""

        for event in input_file:
            try:
                self.event = json.loads(event)
            except (json.JSONDecodeError, TypeError):
                self._log_error("Invalid event! Not parsable JSON!")
                continue
            if not isinstance(self.event, dict):
                self._log_error("Invalid event! Not a dictionary!")
                continue
            converter = self._select_converter()
            if not converter:
                continue
            yield converter.convert(self.event)

    def _select_converter(self):
        """Return a xAPI converter that matches the event"""

        event_source = self.event.get("event_source", None)
        if not event_source:
            self._log_error("Invalid event! Missing event_source!")
            return None
        if event_source == "server":
            return self._select_server_converter()
        self._log_error("No matching xAPI converter found!")
        return None

    def _select_server_converter(self):
        """Return a xAPI server converter that matches the event"""

        event_type = self.event.get("event_type", None)
        context = self.event.get("context", None)
        if not event_type or not context:
            self._log_error("Invalid event! Missing event_type or context!")
            return None
        if not isinstance(context, dict):
            self._log_error("Invalid event! Context not a dictionary!")
            return None
        if event_type == context.get("path", None):
            return self.converters[Converters.SERVER]
        self._log_error("No matching server xAPI converter found!")
        return None

    def _log_error(self, message):
        logger.error(message)
        logger.debug("For Event : %s", self.event)
