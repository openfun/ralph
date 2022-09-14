"""Ralph tracking logs parsers."""

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

        Parameters:
            input_file (file-like): The log file to parse.

        Yields:
            event: raw event as extracted from its container.
        """


class GELFParser(BaseParser):
    """GELF formatted logs parser.

    Documentation of the GELF log format can be found in the Graylog project's
    documentation: https://docs.graylog.org/en/latest/pages/gelf.html
    """

    name = "gelf"

    def parse(self, input_file):
        """Parse GELF formatted logs (one JSON string event per row).

        Parameters:
            input_file (file-like): The log file to parse.

        Yields:
            event: Events raw short_message string.
        """

        logger.info("Parsing: %s", input_file)

        for event in input_file:
            try:
                yield json.loads(event)["short_message"]
            except (json.JSONDecodeError, TypeError) as err:
                msg = "Input event '%s' is not a valid JSON string! It will be ignored."
                logger.error(msg, event)
                logger.debug("Raised error was: %s", err)
            except KeyError as err:
                msg = (
                    "Input event '%s' doesn't comply with GELF format! "
                    "It will be ignored."
                )
                logger.error(msg, event)
                logger.debug("Raised error was: %s", err)


class ElasticSearchParser(BaseParser):
    """ElasticSearch JSON document parser."""

    name = "es"

    def parse(self, input_file):
        """Parse Elasticsearch JSON documents.

        Parameters:
            input_file (file-like): The file containing Elasticsearch JSON documents.

        Yields:
            document: ElasticSearch documents `_source` field content.
        """

        logger.info("Parsing: %s", input_file)

        for document in input_file:
            try:
                yield json.dumps(json.loads(document)["_source"])
            except (json.JSONDecodeError, TypeError) as err:
                msg = "Document '%s' is not a valid JSON string! It will be ignored."
                logger.error(msg, document)
                logger.debug("Raised error was: %s", err)
            except KeyError as err:
                msg = "Document '%s' has no `_source` field! It will be ignored."
                logger.error(msg, document)
                logger.debug("Raised error was: %s", err)
