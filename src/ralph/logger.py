""""Ralph logging manager"""

from logging.config import dictConfig

from ralph.defaults import LOGGING_CONFIG
from ralph.exceptions import ConfigurationException


def configure_logging():
    """Set up Ralph logging configuration"""

    try:
        dictConfig(LOGGING_CONFIG)
    except Exception as error:
        raise ConfigurationException("Improperly configured logging") from error
