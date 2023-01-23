"""Ralph logging manager."""

import logging
from rich import traceback, pretty
from rich.logging import RichHandler
from rich.console import Console

import click
from ralph.conf import settings
from ralph.exceptions import ConfigurationException


def configure_logging():
    """Set up Ralph logging configuration."""
    try:
        console = Console(color_system="standard")
        logging.basicConfig(
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=console)]
        )
        traceback.install(show_locals=True, suppress=[click])
        pretty.install()
    except Exception as error:
        raise ConfigurationException("Improperly configured logging") from error
