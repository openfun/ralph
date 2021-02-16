"""
Ralph tracking logs parsers.
"""

import json
import logging
from abc import ABC, abstractmethod

from .defaults import DEFAULT_GELF_PARSER_CHUNCK_SIZE

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Base tracking logs parser."""

    name = "base"

    @abstractmethod
    def parse(self, input_file, chunksize=1):
        """Parse GELF formatted logs (one json string event per row).

        Args:
            input_file (string): Path to the log file to parse.
            chunksize (int): The amount of log records to process at a time.

        Yields:
            event: raw event as extracted from its container

        """


class GELFParser(BaseParser):
    """GELF formatted logs parser.

    Documentation of the GELF log format can be found in the Graylog project's
    documentation: https://docs.graylog.org/en/latest/pages/gelf.html
    """

    name = "gelf"

    def parse(self, input_file, chunksize=DEFAULT_GELF_PARSER_CHUNCK_SIZE):
        """Parse GELF formatted logs (one json string event per row).

        Args:
            input_file (string): Path to the log file to parse (could be
                gunzipped).
            chunksize (int): The amount of log records to process at a time. A
                value between 3.000 and 10.000 seems to be a reasonnable choice
                to parse 1.5M records in a few minutes (typically 2 or 3
                minutes on a modern computer).

        Yields:
            event: events raw short_message string

        """
        logger.info("Parsing: %s", input_file)

        for event in input_file:
            try:
                yield json.loads(event)["short_message"]
            except (json.JSONDecodeError, TypeError) as err:
                logger.error(
                    "Input event '%s' is not a valid JSON string! It will be ignored.",
                    event,
                )
                logger.debug("Raised error was: %s", err)
            except KeyError as err:
                logger.error(
                    "Input event '%s' doesn't comply with GELF format! It will be ignored.",
                    event,
                )
                logger.debug("Raised error was: %s", err)
