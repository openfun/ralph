"""
Ralph tracking logs parsers.
"""

import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)


class BaseParser:
    """Base tracking logs parser."""

    def parse(self, input_file, filters=None, chunksize=1):
        """Parse a log file and convert it to DataFrames.

        Args:
            input_file (string): Path to the log file to parse.
            filters (list): A list of functions to apply on parsed results to
                filter them.
            chunksize (int): The amount of log records to process at a time.

        Yields:
            DataFrame: parsed and filtered events from the current file chunk.

        """
        raise NotImplementedError


class GELFParser(BaseParser):
    """GELF formatted logs parser.

    Documentation of the GELF log format can be found in the Graylog project's
    documentation: https://docs.graylog.org/en/latest/pages/gelf.html
    """

    def parse(self, input_file, filters=None, chunksize=10000):
        """Parse GELF formatted logs (one json string event per row).

        Args:
            input_file (string): Path to the log file to parse (could be
                gunzipped).
            filters (list): A list of functions to apply on parsed results to
                filter them.
            chunksize (int): The amount of log records to process at a time. A
                value between 3.000 and 10.000 seems to be a reasonnable choice
                to parse 1.5M records in a few minutes (typically 2 or 3
                minutes on a modern computer).

        Yields:
            DataFrame: parsed and filtered events from the current file chunk.

        """
        logger.info("Parsing: %s", input_file)

        if not os.path.exists(input_file):
            msg = "Input GELF log file '%s' does not exist"
            logger.error(msg, input_file)
            raise OSError(msg % (input_file))

        filters = filters or []

        chunks = pd.read_json(input_file, lines=True, chunksize=chunksize)
        for chunk in chunks:
            events = pd.read_json("\n".join(chunk["short_message"]), lines=True)
            logger.debug("Events before filtering: %d", len(events))

            for _filter in filters:
                logger.debug("Current filter: %s", _filter.__name__)
                if events.empty:
                    logger.warning(
                        "Current chunk contains no events, will stop filtering."
                    )
                    break
                events = _filter(events)
                logger.debug("Filter: %s (events: %d)", _filter.__name__, len(events))

            yield events
