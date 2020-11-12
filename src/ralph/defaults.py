"""Default configurations for Ralph"""

from enum import Enum
from os import environ
from pathlib import Path

from click import get_app_dir


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


APP_DIR = Path(environ.get("RALPH_APP_DIR", get_app_dir("ralph")))
DEFAULT_GELF_PARSER_CHUNCK_SIZE = 5000
DEFAULT_BACKEND_CHUNCK_SIZE = 500
ENVVAR_PREFIX = "RALPH"
HISTORY_FILE = Path(environ.get("RALPH_HISTORY_FILE", APP_DIR / "history.json"))
FS_STORAGE_DEFAULT_PATH = Path("./archives")
