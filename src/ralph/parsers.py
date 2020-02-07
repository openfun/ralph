"""
Ralph tracking logs parsers.
"""

import logging

import pandas as pd

from .exceptions import EmptyEventsCollection

logger = logging.getLogger(__name__)


class BaseParser:
    """Base tracking logs parser."""

    def parse(self, input_file, filters=None, chunksize=1):
        """Parse GELF formatted logs (one json string event per row).

        Args:
            input_file (string): Path to the log file to parse.
            filters (list): A list of functions to apply on parsed results to
                filter them.
            chunksize (int): The amount of log records to process at a time.

        Returns:
            Parser implementation should return a pandas DataFrame object with
            all parsed and filtered events.

        """
        raise NotImplementedError


class GELFParser(BaseParser):
    """GELF formatted logs parser.

    Documentation of the GELF log format can be found in the Graylog project's
    documentation: https://docs.graylog.org/en/latest/pages/gelf.html
    """

    def parse(self, input_file, filters=None, chunksize=50000):
        """Parse GELF formatted logs (one json string event per row).

        Args:
            input_file (string): Path to the log file to parse (could be
                gunzipped).
            filters (list): A list of functions to apply on parsed results to
                filter them.
            chunksize (int): The amount of log records to process at a time. A
                value between 10.000 and 100.000 seems to be a reasonnable
                choice to parse 1.5M records in a few minutes (typically 2 or 3
                minutes on a modern computer).

        Returns:
            A pandas DataFrame object with all parsed and filtered events.

        """
        logger.info("Parsing: %s", input_file)

        filters = filters or []
        events = pd.DataFrame()

        chunks = pd.read_json(input_file, lines=True, chunksize=chunksize)
        for chunk in chunks:
            records = pd.read_json("\n".join(chunk["_msg"]), lines=True)
            logger.debug("Records before filtering: %d", len(records))

            for _filter in filters:
                try:
                    records = _filter(records)
                except EmptyEventsCollection:
                    logger.warning(
                        "Current chunk contains no records, will stop filtering."
                    )
                    break
                logger.debug("Filter: %s (records: %d)", _filter.__name__, len(records))

            events = events.append(records, ignore_index=True, sort=False)
            logger.debug("Total events: %d", len(events))

        logger.info("Parsed: %d events (after filtering)", len(events))
        return events
