"""Default configurations for Ralph"""

from enum import Enum
from os import environ
from pathlib import Path

import yaml
from click import get_app_dir

from ralph.exceptions import ConfigurationException


class DatabaseBackends(Enum):
    """Enumerate active database backend modules.

    Adding an entry to this enum will make it available to the CLI.
    """

    ES = "ralph.backends.database.es.ESDatabase"


class Parsers(Enum):
    """Enumerate active parsers modules.

    Adding an entry to this enum will make it available to the CLI.
    """

    GELF = "ralph.parsers.GELFParser"


class StorageBackends(Enum):
    """Enumerate active storage backend modules.

    Adding an entry to this enum will make it available to the CLI.
    """

    LDP = "ralph.backends.storage.ldp.LDPStorage"
    FS = "ralph.backends.storage.fs.FSStorage"
    SWIFT = "ralph.backends.storage.swift.SwiftStorage"


def load_config(config_file_path):
    """Return a dictionary representing Ralph's configuration."""

    try:
        with open(config_file_path) as config_file:
            return yaml.safe_load(config_file)
    except yaml.scanner.ScannerError as exc:
        raise ConfigurationException("Configuration could not be loaded") from exc
    except FileNotFoundError:
        return None


def config(key, default_value):
    """
    Get a value based on its key returning the first of (in order):
        1. Environment
        2. Config file
        3. default_value
    """

    value = environ.get(key, None)
    if value is not None:
        return value

    if CONFIG is not None and key in CONFIG:
        return CONFIG[key]

    return default_value


DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "propagate": True,
    "formatters": {
        "ralph": {"format": "%(asctime)-23s %(levelname)-8s %(name)-8s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "stream": "ext://sys.stderr",
            "formatter": "ralph",
        },
    },
    "loggers": {
        "ralph": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "swiftclient": {
            "handlers": ["console"],
            "level": "ERROR",
        },
    },
}

APP_DIR = Path(environ.get("RALPH_APP_DIR", get_app_dir("ralph")))
CONFIG_FILE = APP_DIR / "config.yml"
CONFIG = load_config(CONFIG_FILE)
ENVVAR_PREFIX = "RALPH"
DEFAULT_BACKEND_CHUNK_SIZE = config("RALPH_DEFAULT_BACKEND_CHUNK_SIZE", 500)
FS_STORAGE_DEFAULT_PATH = Path(
    config("RALPH_FS_STORAGE_DEFAULT_PATH", APP_DIR / "archives")
)
HISTORY_FILE = Path(config("RALPH_HISTORY_FILE", APP_DIR / "history.json"))
LOGGING_CONFIG = config("RALPH_LOGGING", DEFAULT_LOGGING_CONFIG)
MODEL_PATH_SEPARATOR = "__"
SENTRY_DSN = config("RALPH_SENTRY_DSN", None)
SWIFT_OS_AUTH_URL = config("RALPH_SWIFT_OS_AUTH_URL", "https://auth.cloud.ovh.net/")
SWIFT_OS_IDENTITY_API_VERSION = config("RALPH_SWIFT_OS_IDENTITY_API_VERSION", "3")
SWIFT_OS_PROJECT_DOMAIN_NAME = config("RALPH_SWIFT_OS_PROJECT_DOMAIN_NAME", "Default")
SWIFT_OS_USER_DOMAIN_NAME = config("RALPH_SWIFT_OS_USER_DOMAIN_NAME", "Default")
CONVERTER_EDX_XAPI_UUID_NAMESPACE = config(
    "RALPH_CONVERTER_EDX_XAPI_UUID_NAMESPACE", None
)
EXECUTION_ENVIRONMENT = config("RALPH_EXECUTION_ENVIRONMENT", "development")
