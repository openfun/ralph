"""Configurations for Ralph."""

import io
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, List, Sequence, Tuple, Union

from pydantic import AnyHttpUrl, AnyUrl, BaseModel, BaseSettings, Extra, Field, root_validator, StrictStr

from ralph.exceptions import ConfigurationException

from .utils import import_string

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

try:
    from click import get_app_dir
except ImportError:
    # If we use Ralph as a library and Click is not installed, we consider the
    # application directory to be the current directory. For non-CLI usage, it
    # has no consequences.
    from unittest.mock import Mock

    get_app_dir = Mock(return_value=".")

MODEL_PATH_SEPARATOR = "__"

NonEmptyStr = Annotated[str, Field(min_length=1)]
NonEmptyStrictStr = Annotated[StrictStr, Field(min_length=1)]

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
    """Pydantic field type validating comma-separated strings or lists/tuples."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(value: Union[str, Sequence[str]]) -> Sequence[str]:
            """Check whether the value is a comma-separated string or a list/tuple."""
            if isinstance(value, (tuple, list)):
                return tuple(value)

            if isinstance(value, str):
                return tuple(value.split(","))

            raise TypeError("Invalid comma-separated list")

        yield validate


class InstantiableSettingsItem(BaseModel):
    """Pydantic model for a settings configuration item that can be instantiated."""

    class Config:  # noqa: D106
        underscore_attrs_are_private = True

    _class_path: str = None

    def get_instance(self, **init_parameters):
        """Return an instance of the settings item class using its `_class_path`."""
        return import_string(self._class_path)(**init_parameters)


class ClientOptions(BaseModel):
    """Pydantic model for additional client options."""

    class Config:  # noqa: D106
        extra = Extra.forbid


class HeadersParameters(BaseModel):
    """Pydantic model for headers parameters."""

    class Config:  # noqa: D106
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

    # class Config:  # noqa: D106 # TODO: done
    #     min_anystr_length = 1

    url: AnyUrl
    is_active: bool
    basic_username: NonEmptyStr
    basic_password: NonEmptyStr
    max_retries: int
    timeout: float


class AuthBackend(str, Enum):
    """Model for valid authentication methods."""

    BASIC = "basic"
    OIDC = "oidc"


class AuthBackends(Tuple[AuthBackend]):
    """Model representing a tuple of authentication backends."""

    @classmethod
    def __get_validators__(cls):
        """Check whether the value is a comma-separated string or a tuple representing
        an AuthBackend.
        """  # noqa: D205

        def validate(
            auth_backends: Union[
                str, AuthBackend, Tuple[AuthBackend], List[AuthBackend]
            ]
        ) -> Tuple[AuthBackend]:
            """Check whether the value is a comma-separated string or a list/tuple."""
            if isinstance(auth_backends, str):
                return tuple(
                    AuthBackend(value.lower()) for value in auth_backends.split(",")
                )

            if isinstance(auth_backends, AuthBackend):
                return (auth_backends,)

            if isinstance(auth_backends, (tuple, list)):
                return tuple(auth_backends)

            raise TypeError("Invalid comma-separated list")

        yield validate


class Settings(BaseSettings):
    """Pydantic model for Ralph's global environment & configuration settings."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING

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
    RUNSERVER_AUTH_BACKENDS: AuthBackends = AuthBackends([AuthBackend.BASIC])
    RUNSERVER_AUTH_OIDC_AUDIENCE: str = None
    RUNSERVER_AUTH_OIDC_ISSUER_URI: AnyHttpUrl = None
    RUNSERVER_BACKEND: Literal[
        "async_es", "async_mongo", "clickhouse", "es", "fs", "mongo"
    ] = "es"
    RUNSERVER_HOST: str = "0.0.0.0"  # noqa: S104
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
    def APP_DIR(self) -> Path:
        """Return the path to Ralph's configuration directory."""
        return self._CORE.APP_DIR

    @property
    def LOCALE_ENCODING(self) -> str:
        """Return Ralph's default locale encoding."""
        return self._CORE.LOCALE_ENCODING

    @root_validator(allow_reuse=True)
    @classmethod
    def check_restriction_compatibility(cls, values):
        """Raise an error if scopes are being used without authority restriction."""
        if values.get("LRS_RESTRICT_BY_SCOPES") and not values.get(
            "LRS_RESTRICT_BY_AUTHORITY"
        ):
            raise ConfigurationException(
                "LRS_RESTRICT_BY_AUTHORITY must be set to True if using "
                "LRS_RESTRICT_BY_SCOPES=True"
            )
        return values


settings = Settings()
