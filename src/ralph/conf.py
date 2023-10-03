"""Configurations for Ralph."""

import io
from enum import Enum
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
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, BaseSettings, Extra, Field

from .utils import import_string

MODEL_PATH_SEPARATOR = "__"


class BaseSettingsConfig:
    """Pydantic model for BaseSettings Configuration."""

    case_sensitive = True
    env_nested_delimiter = "__"
    env_prefix = "RALPH_"


class CoreSettings(BaseSettings):
    """Pydantic model for Ralph's core settings."""

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
        """Returns an instance of the settings item class using its `_class_path`."""
        return import_string(self._class_path)(**init_parameters)


# Active database backend Settings.


class ClientOptions(BaseModel):
    """Pydantic model for additional client options."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.forbid


class ClickhouseClientOptions(ClientOptions):
    """Pydantic model for `clickhouse` client options."""

    date_time_input_format: str = "best_effort"
    allow_experimental_object_type: Literal[0, 1] = None


class ESClientOptions(ClientOptions):
    """Pydantic model for Elasticsearch additional client options."""

    ca_certs: Path = None
    verify_certs: bool = None


class ClickhouseDatabaseBackendSettings(InstantiableSettingsItem):
    """Pydantic model for ClickHouse database backend configuration settings."""

    _class_path: str = "ralph.backends.database.clickhouse.ClickHouseDatabase"

    HOST: str = "localhost"
    PORT: int = 8123
    DATABASE: str = "xapi"
    EVENT_TABLE_NAME: str = "xapi_events_all"
    USERNAME: str = None
    PASSWORD: str = None
    CLIENT_OPTIONS: ClickhouseClientOptions = None


class MongoClientOptions(ClientOptions):
    """Pydantic model for MongoDB additional client options."""

    document_class: str = None
    tz_aware: bool = None


class ESDatabaseBackendSettings(InstantiableSettingsItem):
    """Pydantic model for Elasticsearch database backend configuration settings."""

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


# Active HTTP backend Settings.


class HeadersParameters(BaseModel):
    """Pydantic model for headers parameters."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.allow


class LRSHeaders(HeadersParameters):
    """Pydantic model for LRS headers."""

    X_EXPERIENCE_API_VERSION: str = Field("1.0.3", alias="X-Experience-API-Version")
    CONTENT_TYPE: str = Field("application/json", alias="content-type")


class LRSHTTPBackendSettings(InstantiableSettingsItem):
    """Pydantic model for LRS HTTP backend configuration settings."""

    _class_path: str = "ralph.backends.http.lrs.LRSHTTP"

    BASE_URL: AnyHttpUrl = Field("http://0.0.0.0:8100")
    USERNAME: str = "ralph"
    PASSWORD: str = "secret"
    HEADERS: LRSHeaders = LRSHeaders()
    STATUS_ENDPOINT: str = "/__heartbeat__"
    STATEMENTS_ENDPOINT: str = "/xAPI/statements"


class HTTPBackendSettings(BaseModel):
    """Pydantic model for HTTP backend configuration settings."""

    LRS: LRSHTTPBackendSettings = LRSHTTPBackendSettings()


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
    ENDPOINT_URL: str = None


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
    HTTP: HTTPBackendSettings = HTTPBackendSettings()
    STORAGE: StorageBackendSettings = StorageBackendSettings()
    STREAM: StreamBackendSettings = StreamBackendSettings()


# Active parser Settings.


class ESParserSettings(InstantiableSettingsItem):
    """Pydantic model for Elasticsearch parser configuration settings."""

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

    class AuthBackend(Enum):
        """Enum of the authentication backends."""
        BASIC = "basic"
        OIDC = "oidc"

    AuthBackends = List[AuthBackend]

    _CORE: CoreSettings = core_settings
    AUTH_FILE: Path = _CORE.APP_DIR / "auth.json"
    AUTH_CACHE_MAX_SIZE = 100
    AUTH_CACHE_TTL = 3600
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
    RUNSERVER_AUTH_BACKEND: AuthBackends = [AuthBackend.BASIC]
    RUNSERVER_AUTH_OIDC_AUDIENCE: str = None
    RUNSERVER_AUTH_OIDC_ISSUER_URI: AnyHttpUrl = None
    RUNSERVER_BACKEND: Literal["clickhouse", "es", "mongo"] = "es"
    RUNSERVER_HOST: str = "0.0.0.0"  # nosec
    RUNSERVER_MAX_SEARCH_HITS_COUNT: int = 100
    RUNSERVER_POINT_IN_TIME_KEEP_ALIVE: str = "1m"
    RUNSERVER_PORT: int = 8100
    LRS_RESTRICT_BY_AUTHORITY: bool = False
    LRS_RESTRICT_BY_SCOPES: bool = False
    SENTRY_CLI_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_DSN: str = None
    SENTRY_IGNORE_HEALTH_CHECKS: bool = False
    SENTRY_LRS_TRACES_SAMPLE_RATE: float = 1.0
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
