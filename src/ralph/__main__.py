#!/usr/bin/env python

"""
Ralph main entrypoint.

This script is a POC for now, we aim to make ralph a nice CLI to use.
"""

import sentry_sdk

from ralph.conf import settings

from . import __version__, cli

if settings.SENTRY_DSN is not None:
    sentry_sdk.init(  # pylint: disable=abstract-class-instantiated
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        release=__version__,
        environment=settings.EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
    )

cli.cli()
