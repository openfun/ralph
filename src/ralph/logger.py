""""Ralph logging manager"""

from logging.config import dictConfig

from ralph.defaults import get_settings
from ralph.exceptions import ConfigurationException


def configure_logging():
    """Set up Ralph logging configuration."""

    try:
        dictConfig(get_settings().LOGGING)
    except Exception as error:
        raise ConfigurationException("Improperly configured logging") from error
