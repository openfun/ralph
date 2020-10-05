"""
Ralph tracking logs parsers.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

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

        if isinstance(input_file, str) and not Path(input_file).exists():
            msg = "Input GELF log file '%s' does not exist"
            logger.error(msg, input_file)
            raise OSError(msg % (input_file))

        chunks = pd.read_json(input_file, lines=True, chunksize=chunksize)
        for chunk in chunks:
            for event in chunk["short_message"].values:
                yield event
