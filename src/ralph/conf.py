"""Configurations for Ralph"""

import io
from pathlib import Path
from typing import Literal, Union

from click import get_app_dir
from pydantic import BaseModel, BaseSettings

from ralph.utils import import_string

MODEL_PATH_SEPARATOR = "__"


class BaseSettingsConfig:
    """Pydantic BaseSettings Configuration."""

    case_sensitive = True
    env_nested_delimiter = "__"
    env_prefix = "RALPH_"


class CoreSettings(BaseSettings):
    """Represents Ralph's core settings."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

    APP_DIR: Path = get_app_dir("ralph")
    LOCALE_ENCODING: str = getattr(io, "LOCALE_ENCODING", "utf8")


core_settings = CoreSettings()


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


class InstantiableSettingsItem(BaseModel):
    """Represents a settings configuration item that can be instantiated."""

    class Config:  # pylint: disable=missing-class-docstring
        underscore_attrs_are_private = True

    _class_path: str = None

    def get_instance(self, **init_parameters):
        """Returns an instance of the settings item class using it's `_class_path`."""

        return import_string(self._class_path)(**init_parameters)


# Active database backend Settings.


class ESDatabaseBackendSettings(InstantiableSettingsItem):
    """Represents the Elasticsearch database backend configuration settings."""

    _class_path: str = "ralph.backends.database.es.ESDatabase"

    HOSTS: CommaSeparatedTuple = ("http://localhost:9200",)
    INDEX: str = "statements"
    CLIENT_OPTIONS: dict = None
    OP_TYPE: Literal["index", "create", "delete", "update"] = "index"


class MongoDatabaseBackendSettings(InstantiableSettingsItem):
    """Represents the Mongo database backend configuration settings."""

    _class_path: str = "ralph.backends.database.mongo.MongoDatabase"

    CONNECTION_URI: str = "mongodb://localhost:27017/"
    DATABASE: str = "statements"
    COLLECTION: str = "marsha"
    CLIENT_OPTIONS: dict = None


class DatabaseBackendSettings(BaseModel):
    """Represents database backend configuration settings."""

    ES: ESDatabaseBackendSettings = ESDatabaseBackendSettings()
    MONGO: MongoDatabaseBackendSettings = MongoDatabaseBackendSettings()


# Active storage backend Settings.


class FSStorageBackendSettings(InstantiableSettingsItem):
    """Represents the FileSystem storage backend configuration settings."""

    _class_path: str = "ralph.backends.storage.fs.FSStorage"

    PATH: str = str(core_settings.APP_DIR / "archives")


class LDPStorageBackendSettings(InstantiableSettingsItem):
    """Represents the LDP storage backend configuration settings."""

    _class_path: str = "ralph.backends.storage.ldp.LDPStorage"

    ENDPOINT: str = None
    APPLICATION_KEY: str = None
    APPLICATION_SECRET: str = None
    CONSUMER_KEY: str = None
    SERVICE_NAME: str = None
    STREAM_ID: str = None


class SWIFTStorageBackendSettings(InstantiableSettingsItem):
    """Represents the SWIFT storage backend configuration settings."""

    _class_path: str = "ralph.backends.storage.swift.SwiftStorage"

    OS_TENANT_ID: str = None
    OS_TENANT_NAME: str = None
    OS_USERNAME: str = None
    OS_PASSWORD: str = None
    OS_REGION_NAME: str = None
    OS_STORAGE_URL: str = None
    OS_USER_DOMAIN_NAME: str = "Default"
    OS_PROJECT_DOMAIN_NAME: str = "Default"
    OS_AUTH_URL: str = "https://auth.cloud.ovh.net/"
    OS_IDENTITY_API_VERSION: str = "3"


class StorageBackendSettings(BaseModel):
    """Represents storage backend configuration settings."""

    LDP: LDPStorageBackendSettings = LDPStorageBackendSettings()
    FS: FSStorageBackendSettings = FSStorageBackendSettings()
    SWIFT: SWIFTStorageBackendSettings = SWIFTStorageBackendSettings()


# Active storage backend Settings.


class WSStreamBackendSettings(InstantiableSettingsItem):
    """Represents the Websocket stream backend configuration settings."""

    _class_path: str = "ralph.backends.stream.ws.WSStream"

    URI: str = None


class StreamBackendSettings(BaseModel):
    """Represents stream backend configuration settings."""

    WS: WSStreamBackendSettings = WSStreamBackendSettings()


# Active backend Settings.


class BackendSettings(BaseModel):
    """Represents backends configuration settings."""

    DATABASE: DatabaseBackendSettings = DatabaseBackendSettings()
    STORAGE: StorageBackendSettings = StorageBackendSettings()
    STREAM: StreamBackendSettings = StreamBackendSettings()


# Active parser Settings.


class ESParserSettings(InstantiableSettingsItem):
    """Represents the Elastisearch parser configuration settings."""

    _class_path: str = "ralph.parsers.ElasticSearchParser"


class GELFParserSettings(InstantiableSettingsItem):
    """Represents the GELF parser configuration settings."""

    _class_path: str = "ralph.parsers.GELFParser"


class ParserSettings(BaseModel):
    """Represents parsers configuration settings."""

    GELF: GELFParserSettings = GELFParserSettings()
    ES: ESParserSettings = ESParserSettings()


class Settings(BaseSettings):
    """Represents Ralph's global environment & configuration settings."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING

    _CORE: CoreSettings = core_settings
    AUTH_FILE: Path = _CORE.APP_DIR / "auth.json"
    BACKENDS: BackendSettings = BackendSettings()
    CONVERTER_EDX_XAPI_UUID_NAMESPACE: str = None
    DEFAULT_BACKEND_CHUNK_SIZE: int = 500
    EXECUTION_ENVIRONMENT: str = "development"
    HISTORY_FILE: Path = _CORE.APP_DIR / "history.json"
    LOGGING: dict = {
        "version": 1,
        "propagate": True,
        "formatters": {
            "ralph": {
                "format": "%(asctime)-23s %(levelname)-8s %(name)-8s %(message)s"
            },
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
    PARSERS: ParserSettings = ParserSettings()
    RUNSERVER_HOST: str = "0.0.0.0"  # nosec
    RUNSERVER_MAX_SEARCH_HITS_COUNT: int = 100
    RUNSERVER_POINT_IN_TIME_KEEP_ALIVE: str = "1m"
    RUNSERVER_PORT: int = 8100
    SENTRY_DSN: str = None

    @property
    def APP_DIR(self) -> Path:  # pylint: disable=invalid-name
        """Returns the path to Ralph's configuration directory."""

        return self._CORE.APP_DIR

    @property
    def LOCALE_ENCODING(self) -> str:  # pylint: disable=invalid-name
        """Returns Ralph's default locale encoding."""

        return self._CORE.LOCALE_ENCODING


settings = Settings()
