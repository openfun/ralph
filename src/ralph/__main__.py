#!/usr/bin/env python

"""
Ralph main entrypoint.

This script is a POC for now, we aim to make ralph a nice CLI to use.
"""

import logging

from ralph.filters import anonymous, empty
from ralph.parsers import GELFParser

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s - %(name)s - %(message)s"
)

GELFParser().parse("data/2020-02-02.gz", filters=[empty, anonymous], chunksize=50000)
