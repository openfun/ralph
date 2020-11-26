#!/usr/bin/env python

"""
Ralph main entrypoint.

This script is a POC for now, we aim to make ralph a nice CLI to use.
"""

import sentry_sdk

from ralph.defaults import EXECUTION_ENVIRONMENT, SENTRY_DSN

from . import __version__, cli

if SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        release=__version__,
        environment=EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
    )

cli.cli()
