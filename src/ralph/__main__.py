#!/usr/bin/env python

"""
Ralph main entrypoint.

This script is a POC for now, we aim to make ralph a nice CLI to use.
"""

import sentry_sdk

from ralph.defaults import get_settings

from . import __version__, cli

if get_settings().SENTRY_DSN is not None:
    sentry_sdk.init(  # pylint: disable=abstract-class-instantiated
        dsn=get_settings().SENTRY_DSN,
        traces_sample_rate=1.0,
        release=__version__,
        environment=get_settings().EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
    )

cli.cli()
