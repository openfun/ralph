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
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, BaseSettings, Extra

from .utils import import_string

MODEL_PATH_SEPARATOR = "__"


class BaseSettingsConfig:
    """Pydantic model for BaseSettings Configuration."""

    case_sensitive = True
    env_nested_delimiter = "__"
    env_prefix = "RALPH_"
    extra = "ignore"


class CoreSettings(BaseSettings):
    """Pydantic model for Ralph's core settings."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

    APP_DIR: Path = get_app_dir("ralph")
    LOCALE_ENCODING: str = getattr(io, "LOCALE_ENCODING", "utf8")


core_settings = CoreSettings()


class CommaSeparatedTuple(str):
    """Pydantic field type validating comma separated strings or lists/tuples."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(value: Union[str, Tuple[str], List[str]]) -> Tuple[str]:
            """Check whether the value is a comma separated string or a list/tuple."""
            if isinstance(value, (tuple, list)):
                return tuple(value)

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


class ClientOptions(BaseModel):
    """Pydantic model for additional client options."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.forbid


class HeadersParameters(BaseModel):
    """Pydantic model for headers parameters."""

    class Config:  # pylint: disable=missing-class-docstring # noqa: D106
        extra = Extra.allow


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

    class AuthBackends(Enum):
        """Enum of the authentication backends."""

        BASIC = "basic"
        OIDC = "oidc"

    _CORE: CoreSettings = core_settings
    AUTH_FILE: Path = _CORE.APP_DIR / "auth.json"
    AUTH_CACHE_MAX_SIZE = 100
    AUTH_CACHE_TTL = 3600
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
    RUNSERVER_AUTH_BACKEND: AuthBackends = AuthBackends.BASIC
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
