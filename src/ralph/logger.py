"""Ralph logging manager."""

from logging.config import dictConfig

from ralph.conf import settings
from ralph.exceptions import ConfigurationException


def configure_logging():
    """Set up Ralph logging configuration."""
    try:
        # console = Console(color_system="standard")
        # logging.basicConfig(
        #     format="%(message)s",
        #     datefmt="[%X]",
        #     handlers=[RichHandler(console=console)]
        # )
        # traceback.install(show_locals=True, suppress=[click])
        # pretty.install()
        dictConfig(settings.LOGGING)
    except Exception as error:
        raise ConfigurationException("Improperly configured logging") from error
