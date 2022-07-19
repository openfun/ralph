"""Default configurations for Ralph"""

import io
from functools import lru_cache
from os import environ
from pathlib import Path
from typing import Any, Literal, Optional, Union

import yaml
from click import get_app_dir
from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable
from pydantic.fields import ModelField

from ralph.backends import BackendTypes
from ralph.exceptions import ConfigurationException
from ralph.utils import import_string

# Backends and Parsers
# Adding an entry to these dictionaries will make it available to the CLI.

# Enumerates active database backend modules.
DATABASE_BACKENDS = {
    "es": "ralph.backends.database.es.ESDatabase",
    "mongo": "ralph.backends.database.mongo.MongoDatabase",
}
# Enumerates active parsers modules.
PARSERS = {
    "gelf": "ralph.parsers.GELFParser",
    "es": "ralph.parsers.ElasticSearchParser",
}
# Enumerates active storage backend modules.
STORAGE_BACKENDS = {
    "ldp": "ralph.backends.storage.ldp.LDPStorage",
    "fs": "ralph.backends.storage.fs.FSStorage",
    "swift": "ralph.backends.storage.swift.SwiftStorage",
}
# Enumerates streaming backend modules.
STREAM_BACKENDS = {"ws": "ralph.backends.stream.ws.WSStream"}
# Enumerates all backend modules.
BACKENDS = DATABASE_BACKENDS | STORAGE_BACKENDS | STREAM_BACKENDS


# Ralph's global constants

APP_DIR = Path(environ.get("RALPH_APP_DIR", get_app_dir("ralph")))
DEFAULT_ENCODING = getattr(io, "LOCALE_ENCODING", "utf8")
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
MODEL_PATH_SEPARATOR = "__"


# Ralph's configuration


def load_config(config_file_path):
    """Return a dictionary representing Ralph's configuration."""

    try:
        with open(config_file_path, encoding=DEFAULT_ENCODING) as config_file:
            return yaml.safe_load(config_file)
    except yaml.scanner.ScannerError as exc:
        raise ConfigurationException("Configuration could not be loaded") from exc
    except FileNotFoundError:
        return None


class CommaSeparatedTuple(str):
    """Represents a pydantic field type validating comma separated strings or tuples."""

    @classmethod
    def __get_validators__(cls):
        def validate(value: Union[str, tuple[str]]) -> tuple[str]:
            """Checks whether the value is a comma separated string or a tuple."""

            if isinstance(value, tuple):
                return value

            if isinstance(value, str):
                return tuple(value.split(","))

            raise TypeError("Invalid comma separated list")

        yield validate


class ConfigFileSettingsSource:
    """Represents a pydantic SettingsSource handling YAML configuration files."""

    __slots__ = ("config",)

    def __init__(self, config_file_path: str):
        """Instantiates the ConfigFileSettingsSource and reads the configration file."""

        self.config: Optional[dict] = load_config(config_file_path)

    def __call__(self, settings: BaseSettings) -> dict[str, Any]:
        """Reads configuration variables suitable for passing to the Model."""

        result: dict[str, Any] = {}

        if not self.config:
            return result

        for field in settings.__fields__.values():
            value: Optional[str] = self.config.get(field.alias)
            if value is not None:
                result[field.alias] = value

        return result


class Settings(BaseSettings):
    """Represents Ralph's global environment & configuration settings."""

    class Config:
        """Pydantic Configuration."""

        case_sensitive = True
        env_prefix = "RALPH_"
        underscore_attrs_are_private = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            """Retuns a tuple of callables that retreive settings values."""

            config_settings = ConfigFileSettingsSource(APP_DIR / "config.yml")
            return init_settings, env_settings, config_settings, file_secret_settings

    AUTH_FILE: Path = APP_DIR / "auth.json"
    CONVERTER_EDX_XAPI_UUID_NAMESPACE: str = None
    DEFAULT_BACKEND_CHUNK_SIZE: int = 500
    HISTORY_FILE: Path = APP_DIR / "history.json"
    LOCALE_ENCODING: str = DEFAULT_ENCODING
    LOGGING: dict = DEFAULT_LOGGING_CONFIG
    SENTRY_DSN: str = None
    EXECUTION_ENVIRONMENT: str = "development"
    RUNSERVER_HOST: str = "0.0.0.0"  # nosec
    RUNSERVER_MAX_SEARCH_HITS_COUNT: int = 100
    RUNSERVER_POINT_IN_TIME_KEEP_ALIVE: str = "1m"
    RUNSERVER_PORT: int = 8100

    # DATABASE BACKENDS
    # ElasticSearch backend
    ES_HOSTS: CommaSeparatedTuple = ("http://localhost:9200",)
    ES_INDEX: str = "statements"
    ES_CLIENT_OPTIONS: dict = None
    ES_OP_TYPE: Literal["index", "create", "delete", "update"] = "index"
    # MongoDB backend
    MONGO_CONNECTION_URI: str = "mongodb://localhost:27017/"
    MONGO_DATABASE: str = "statements"
    MONGO_COLLECTION: str = "marsha"
    MONGO_CLIENT_OPTIONS: dict = None

    # STORAGE BACKENDS
    # FileSystem backend
    FS_PATH: str = str(APP_DIR / "archives")
    # OVH's LDP backend
    LDP_ENDPOINT: str = None
    LDP_APPLICATION_KEY: str = None
    LDP_APPLICATION_SECRET: str = None
    LDP_CONSUMER_KEY: str = None
    LDP_SERVICE_NAME: str = None
    LDP_STREAM_ID: str = None
    # Swift backend
    SWIFT_OS_TENANT_ID: str = None
    SWIFT_OS_TENANT_NAME: str = None
    SWIFT_OS_USERNAME: str = None
    SWIFT_OS_PASSWORD: str = None
    SWIFT_OS_REGION_NAME: str = None
    SWIFT_OS_STORAGE_URL: str = None
    SWIFT_OS_USER_DOMAIN_NAME: str = "Default"
    SWIFT_OS_PROJECT_DOMAIN_NAME: str = "Default"
    SWIFT_OS_AUTH_URL: str = "https://auth.cloud.ovh.net/"
    SWIFT_OS_IDENTITY_API_VERSION: str = "3"

    # STREAM BACKENDS
    # WebSocket backend
    WS_URI: str = None

    @classmethod
    @lru_cache()
    def get_fields_by_backend(cls) -> dict[str, dict[str, ModelField]]:
        """Returns a dictionary containing for each backend all available fields."""

        fields_by_backend = {backend_name: {} for backend_name in BACKENDS}
        for name, model_field in cls.__fields__.items():
            prefix = name.partition("_")[0].lower()
            if BACKENDS.get(prefix):
                fields_by_backend[prefix][name] = model_field
        return fields_by_backend

    @staticmethod
    def get_backend_type(backend_name: str):
        """Returns the backend type from a backend name."""

        if backend_name in STORAGE_BACKENDS:
            return BackendTypes.STORAGE
        if backend_name in DATABASE_BACKENDS:
            return BackendTypes.DATABASE
        if backend_name in STREAM_BACKENDS:
            return BackendTypes.STREAM
        return None

    def get_backend_instance(self, backend_name: str, **init_parameters):
        """Return a backend instance given backend-name-prefixed init parameters."""

        parameters = {
            field_name.partition("_")[2].lower(): getattr(self, field_name)
            for field_name in self.get_fields_by_backend()[backend_name]
        }
        names = filter(lambda p: p.startswith(backend_name), init_parameters.keys())
        parameters.update(
            {
                name.replace(f"{backend_name}_", ""): init_parameters[name]
                for name in names
            }
        )
        return import_string(BACKENDS.get(backend_name))(**parameters)


@lru_cache()
def get_settings(*args, **kwargs) -> Settings:
    """Returns Ralph's settings. Passes all arguments to the Settings class."""

    return Settings(*args, **kwargs)
