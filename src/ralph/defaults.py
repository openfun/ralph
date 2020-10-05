"""Default configurations for Ralph"""

from enum import Enum
from os import environ
from pathlib import Path

from .utils import import_string


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


APP_DIR = Path(environ.get("RALPH_APP_DIR", Path(environ.get("HOME")) / ".ralph"))
AVAILABLE_PARSERS = (lambda: (import_string(parser.value).name for parser in Parsers))()
AVAILABLE_STORAGE_BACKENDS = (
    lambda: (import_string(backend.value).name for backend in StorageBackends)
)()
ENVVAR_PREFIX = "RALPH"
HISTORY_FILE = Path(environ.get("RALPH_HISTORY_FILE", APP_DIR / "history.json"))
