#!/usr/bin/env python

"""
Ralph main entrypoint.

This script is a POC for now, we aim to make ralph a nice CLI to use.
"""

import logging

from ralph.filters import anonymous
from ralph.parsers import GELFParser

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger()

for c, events in enumerate(
    GELFParser().parse("data/2020-02-02.gz", filters=[anonymous], chunksize=5000)
):
    logger.info("Chunk[%06d]: %d events (after filtering)", c, len(events))
