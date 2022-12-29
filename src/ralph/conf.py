"""Configurations for Ralph."""

import io
from pathlib import Path
from typing import List, Tuple, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

try:
    from click import get_app_dir
except ImportError:
    # If we use Ralph as a library and Click is not installed, we consider the
    # application directory to be the current directory. For non-CLI usage, it
    # has no consequences.
    from unittest.mock import Mock

    get_app_dir = Mock(return_value=".")
from pydantic import AnyUrl, BaseModel, BaseSettings, Extra

from .utils import import_string

MODEL_PATH_SEPARATOR = "__"


class BaseSettingsConfig:
    """Pydantic model for BaseSettings Configuration."""

    case_sensitive = True
    env_nested_delimiter = "__"
    env_prefix = "RALPH_"


class CoreSettings(BaseSettings):
    """Pydantice model for Ralph's core settings."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

    APP_DIR: Path = get_app_dir("ralph")
    LOCALE_ENCODING: str = getattr(io, "LOCALE_ENCODING", "utf8")


core_settings = CoreSettings()


class CommaSeparatedTuple(str):
    """Pydantic field type validating comma separated strings or tuples."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(value: Union[str, Tuple[str]]) -> Tuple[str]:
            """Checks whether the value is a comma separated string or a tuple."""
            if isinstance(value, tuple):
                return value

            if isinstance(value, str):
                return tuple(value.split(","))

            raise TypeError("Invalid comma separated list")

        yield validate


class InstantiableSettingsItem(BaseModel):
    """Pydantic model for a settings configuration item that can be instantiated."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        underscore_attrs_are_private = True

    _class_path: str = None

    def get_instance(self, **init_parameters):
        """Returns an instance of the settings item class using it's `_class_path`."""
        return import_string(self._class_path)(**init_parameters)


# Active database backend Settings.


class ClickhouseDatabaseBackendSettings(InstantiableSettingsItem):
    """Pydantic model for ClickHouse database backend configuration settings."""

    _class_path: str = "ralph.backends.database.clickhouse.ClickHouseDatabase"

    HOST: str = "localhost"
    PORT: int = 8123
    DATABASE: str = "xapi"
    EVENT_TABLE_NAME: str = "xapi_events_all"
    CLIENT_OPTIONS: dict = None


class ClientOptions(BaseModel):
    """Pydantic model for additionnal client options."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.forbid


class ESClientOptions(ClientOptions):
    """Pydantic model for Elasticsearch additionnal client options."""

    ca_certs: Path = None
    verify_certs: bool = None


class MongoClientOptions(ClientOptions):
    """Pydantic model for MongoDB additionnal client options."""

    document_class: str = None
    tz_aware: bool = None


class ESDatabaseBackendSettings(InstantiableSettingsItem):
    """Pydantic modelf for Elasticsearch database backend configuration settings."""

    _class_path: str = "ralph.backends.database.es.ESDatabase"

    HOSTS: CommaSeparatedTuple = ("http://localhost:9200",)
    INDEX: str = "statements"
    CLIENT_OPTIONS: ESClientOptions = ESClientOptions()
    OP_TYPE: Literal["index", "create", "delete", "update"] = "index"


class MongoDatabaseBackendSettings(InstantiableSettingsItem):
    """Pydantic model for Mongo database backend configuration settings."""

    _class_path: str = "ralph.backends.database.mongo.MongoDatabase"

    CONNECTION_URI: str = "mongodb://localhost:27017/"
    DATABASE: str = "statements"
    COLLECTION: str = "marsha"
    CLIENT_OPTIONS: MongoClientOptions = MongoClientOptions()


class DatabaseBackendSettings(BaseModel):
    """Pydantic model for database backend configuration settings."""

    ES: ESDatabaseBackendSettings = ESDatabaseBackendSettings()
    MONGO: MongoDatabaseBackendSettings = MongoDatabaseBackendSettings()
    CLICKHOUSE: ClickhouseDatabaseBackendSettings = ClickhouseDatabaseBackendSettings()


# Active storage backend Settings.


class FSStorageBackendSettings(InstantiableSettingsItem):
    """Pydantic model for FileSystem storage backend configuration settings."""

    _class_path: str = "ralph.backends.storage.fs.FSStorage"

    PATH: str = str(core_settings.APP_DIR / "archives")


class LDPStorageBackendSettings(InstantiableSettingsItem):
    """Pydantic model for LDP storage backend configuration settings."""

    _class_path: str = "ralph.backends.storage.ldp.LDPStorage"

    ENDPOINT: str = None
    APPLICATION_KEY: str = None
    APPLICATION_SECRET: str = None
    CONSUMER_KEY: str = None
    SERVICE_NAME: str = None
    STREAM_ID: str = None


class SWIFTStorageBackendSettings(InstantiableSettingsItem):
    """Pydantic model for SWIFT storage backend configuration settings."""

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


class S3StorageBackendSettings(InstantiableSettingsItem):
    """Represents the S3 storage backend configuration settings."""

    _class_path: str = "ralph.backends.storage.s3.S3Storage"

    ACCESS_KEY_ID: str = None
    SECRET_ACCESS_KEY: str = None
    SESSION_TOKEN: str = None
    DEFAULT_REGION: str = None
    BUCKET_NAME: str = None


class StorageBackendSettings(BaseModel):
    """Pydantic model for storage backend configuration settings."""

    LDP: LDPStorageBackendSettings = LDPStorageBackendSettings()
    FS: FSStorageBackendSettings = FSStorageBackendSettings()
    SWIFT: SWIFTStorageBackendSettings = SWIFTStorageBackendSettings()
    S3: S3StorageBackendSettings = S3StorageBackendSettings()


# Active storage backend Settings.


class WSStreamBackendSettings(InstantiableSettingsItem):
    """Pydantic model for Websocket stream backend configuration settings."""

    _class_path: str = "ralph.backends.stream.ws.WSStream"

    URI: str = None


class StreamBackendSettings(BaseModel):
    """Pydantic model for stream backend configuration settings."""

    WS: WSStreamBackendSettings = WSStreamBackendSettings()


# Active backend Settings.


class BackendSettings(BaseModel):
    """Pydantic model for backends configuration settings."""

    DATABASE: DatabaseBackendSettings = DatabaseBackendSettings()
    STORAGE: StorageBackendSettings = StorageBackendSettings()
    STREAM: StreamBackendSettings = StreamBackendSettings()


# Active parser Settings.


class ESParserSettings(InstantiableSettingsItem):
    """Pydantic model for Elastisearch parser configuration settings."""

    _class_path: str = "ralph.parsers.ElasticSearchParser"


class GELFParserSettings(InstantiableSettingsItem):
    """Pydantic model for GELF parser configuration settings."""

    _class_path: str = "ralph.parsers.GELFParser"


class ParserSettings(BaseModel):
    """Pydantic model for parsers configuration settings."""

    GELF: GELFParserSettings = GELFParserSettings()
    ES: ESParserSettings = ESParserSettings()


class XapiForwardingConfigurationSettings(BaseModel):
    """Pydantic model for xAPI forwarding configuration item."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        min_anystr_length = 1

    url: AnyUrl
    is_active: bool
    basic_username: str
    basic_password: str
    max_retries: int
    timeout: float


class Settings(BaseSettings):
    """Pydantic model for Ralph's global environment & configuration settings."""

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
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
            },
        },
    }
    PARSERS: ParserSettings = ParserSettings()
    RUNSERVER_BACKEND: Literal["clickhouse", "es", "mongo"] = "es"
    RUNSERVER_HOST: str = "0.0.0.0"  # nosec
    RUNSERVER_MAX_SEARCH_HITS_COUNT: int = 100
    RUNSERVER_POINT_IN_TIME_KEEP_ALIVE: str = "1m"
    RUNSERVER_PORT: int = 8100
    SENTRY_DSN: str = None
    SENTRY_CLI_TRACES_SAMPLE_RATE = 1.0
    SENTRY_LRS_TRACES_SAMPLE_RATE = 0.1
    XAPI_FORWARDINGS: List[XapiForwardingConfigurationSettings] = []

    @property
    def APP_DIR(self) -> Path:  # pylint: disable=invalid-name
        """Returns the path to Ralph's configuration directory."""
        return self._CORE.APP_DIR

    @property
    def LOCALE_ENCODING(self) -> str:  # pylint: disable=invalid-name
        """Returns Ralph's default locale encoding."""
        return self._CORE.LOCALE_ENCODING


settings = Settings()
