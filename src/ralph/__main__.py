#!/usr/bin/env python

"""
Ralph main entrypoint.

This script is a POC for now, we aim to make ralph a nice CLI to use.
"""

import logging

from ralph.exceptions import IgnoredEvent, NotImplementedStatementType
from ralph.filters import anonymous
from ralph.formatters.xapi.statements import factory as xapi
from ralph.parsers import GELFParser
from ralph.transformers import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

for c, events in enumerate(
    GELFParser().parse(
        "data/2020-02-02.gz",
        filters=[anonymous],
        transformers=[datetime],
        chunksize=100,
    )
):
    logger.info("Chunk[%06d]: %d events (after filtering)", c, len(events))

    for event in events.itertuples(name="Event"):
        try:
            statement = xapi(event)
        except NotImplementedStatementType:
            logger.warning("Ignored unsupported event type: %s", event.event_type)
            continue
        except IgnoredEvent:
            logger.warning("Ignored event: %s", event)
            continue
        else:
            logger.info(event)
            logger.info("%s: %s", statement.__class__.__name__, statement)
