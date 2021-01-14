"""
Ralph tracking logs parsers.
"""

import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Base tracking logs parser."""

    name = "base"

    @abstractmethod
    def parse(self, input_file):
        """Parse GELF formatted logs (one JSON string event per row).

        Args:
            input_file (string): Path to the log file to parse.

        Yields:
            event: raw event as extracted from its container

        """


class GELFParser(BaseParser):
    """GELF formatted logs parser.

    Documentation of the GELF log format can be found in the Graylog project's
    documentation: https://docs.graylog.org/en/latest/pages/gelf.html
    """

    name = "gelf"

    def parse(self, input_file):
        """Parse GELF formatted logs (one JSON string event per row).

        Args:
            input_file (file): log file to parse

        Yields:
            event: events raw short_message string

        """
        logger.info("Parsing: %s", input_file)

        for event in input_file:
            try:
                yield json.loads(event)["short_message"]
            except (json.JSONDecodeError, TypeError, KeyError) as err:
                logger.error(
                    "Invalid event! Not JSON parsable or short_message missing!"
                )
                logger.debug("%s%s", type(err), err)
