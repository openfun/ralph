"""Configurations for Ralph."""

import io
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, List, Optional, Sequence, Union, Tuple

from pydantic import AfterValidator, model_validator, ConfigDict, AnyHttpUrl, AnyUrl, BaseModel, parse_obj_as

from ralph.exceptions import ConfigurationException

from .utils import import_string
from pydantic_settings import BaseSettings, SettingsConfigDict

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


class BaseSettingsConfig:
    """Pydantic model for BaseSettings Configuration."""

    case_sensitive = True
    env_nested_delimiter = "__"
    env_prefix = "RALPH_"
    extra = "ignore"


class CoreSettings(BaseSettings):
    """Pydantic model for Ralph's core settings."""

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

    APP_DIR: Path = get_app_dir("ralph")
    LOCALE_ENCODING: str = getattr(io, "LOCALE_ENCODING", "utf8")


core_settings = CoreSettings()


# class CommaSeparatedTuple(str):
#     """Pydantic field type validating comma separated strings or lists/tuples."""

#     @classmethod
#     # TODO[pydantic]: We couldn't refactor `__get_validators__`, please create the `__get_pydantic_core_schema__` manually.
#     # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
#     def __get_validators__(cls):  # noqa: D105
#         def validate(value: Union[str, Sequence[str]]) -> Sequence[str]:
#             """Check whether the value is a comma separated string or a list/tuple."""
#             if isinstance(value, (tuple, list)):
#                 return tuple(value)

#             if isinstance(value, str):
#                 return tuple(value.split(","))

#             raise TypeError("Invalid comma separated list")

#         yield validate

def validate_comma_separated_tuple(value: Union[str, Tuple[str, ...]]) -> Tuple[str]:
    """Checks whether the value is a comma separated string or a tuple."""

    if isinstance(value, tuple):
        return value

    if isinstance(value, str):
        return tuple(value.split(","))

    raise TypeError("Invalid comma separated list")

CommaSeparatedTuple = Annotated[Union[str, Tuple[str, ...]], AfterValidator(validate_comma_separated_tuple)]


class InstantiableSettingsItem(BaseModel):
    """Pydantic model for a settings configuration item that can be instantiated."""
    # TODO[pydantic]: The following keys were removed: `underscore_attrs_are_private`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = SettingsConfigDict(underscore_attrs_are_private=True)

    _class_path: str = None

    def get_instance(self, **init_parameters):
        """Return an instance of the settings item class using its `_class_path`."""
        return import_string(self._class_path)(**init_parameters)


class ClientOptions(BaseModel):
    """Pydantic model for additional client options."""
    model_config = ConfigDict(extra="forbid")


class HeadersParameters(BaseModel):
    """Pydantic model for headers parameters."""
    model_config = ConfigDict(extra="allow")


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
    model_config = ConfigDict(str_min_length=1)

    url: AnyUrl
    is_active: bool
    basic_username: str
    basic_password: str
    max_retries: int
    timeout: float


class AuthBackend(Enum):
    """Model for valid authentication methods."""

    BASIC = "Basic"
    OIDC = "OIDC"


# class AuthBackends(str):
#     """Model representing a list of authentication backends."""

#     @classmethod
#     # TODO[pydantic]: We couldn't refactor `__get_validators__`, please create the `__get_pydantic_core_schema__` manually.
#     # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
#     def __get_validators__(cls):  # noqa: D105
#         """Checks whether the value is a comma separated string or a tuple representing
#         an AuthBackend."""

#         def validate(
#             value: Union[AuthBackend, Tuple[AuthBackend], List[AuthBackend]]
#         ) -> Tuple[AuthBackend]:
#             """Check whether the value is a comma separated string or a list/tuple."""
#             if isinstance(value, (tuple, list)):
#                 return tuple(AuthBackend(value))

#             if isinstance(value, str):
#                 return tuple(AuthBackend(val) for val in value.split(","))

#             raise TypeError("Invalid comma separated list")

#         yield validate

def validate_auth_backends(
    value: Union[AuthBackend, Tuple[AuthBackend], List[AuthBackend]]
) -> Tuple[AuthBackend]:
    """Check whether the value is a comma separated string or a list/tuple."""
    if isinstance(value, (tuple, list)):
        return tuple(AuthBackend(value))

    if isinstance(value, str):
        return tuple(AuthBackend(val) for val in value.split(","))

    raise TypeError("Invalid comma separated list")

AuthBackends = Annotated[Union[str, Tuple[str, ...], List[str]], AfterValidator(validate_auth_backends)]


class Settings(BaseSettings):
    """Pydantic model for Ralph's global environment & configuration settings."""

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING

    _CORE: CoreSettings = core_settings
    AUTH_FILE: Path = _CORE.APP_DIR / "auth.json"
    AUTH_CACHE_MAX_SIZE: int = 100
    AUTH_CACHE_TTL: int = 3600
    CONVERTER_EDX_XAPI_UUID_NAMESPACE: Optional[str] = None
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
    RUNSERVER_AUTH_BACKENDS: AuthBackends = parse_obj_as(AuthBackends, 'Basic')
    RUNSERVER_AUTH_OIDC_AUDIENCE: str = None
    RUNSERVER_AUTH_OIDC_ISSUER_URI: AnyHttpUrl = None
    RUNSERVER_BACKEND: Literal[
        "async_es", "async_mongo", "clickhouse", "es", "mongo"
    ] = "es"
    RUNSERVER_HOST: str = "0.0.0.0"  # nosec
    RUNSERVER_MAX_SEARCH_HITS_COUNT: int = 100
    RUNSERVER_POINT_IN_TIME_KEEP_ALIVE: str = "1m"
    RUNSERVER_PORT: int = 8100
    LRS_RESTRICT_BY_AUTHORITY: bool = False
    LRS_RESTRICT_BY_SCOPES: bool = False
    SENTRY_CLI_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_DSN: Optional[str] = None
    SENTRY_IGNORE_HEALTH_CHECKS: bool = False
    SENTRY_LRS_TRACES_SAMPLE_RATE: float = 1.0
    XAPI_FORWARDINGS: List[XapiForwardingConfigurationSettings] = []

    @property
    def APP_DIR(self) -> Path:  # pylint: disable=invalid-name
        """Return the path to Ralph's configuration directory."""
        return self._CORE.APP_DIR

    @property
    def LOCALE_ENCODING(self) -> str:  # pylint: disable=invalid-name
        """Return Ralph's default locale encoding."""
        return self._CORE.LOCALE_ENCODING

    @model_validator(mode='after')
    @classmethod
    def check_restriction_compatibility(cls, values):
        """Raise an error if scopes are being used without authority restriction."""
        if values.LRS_RESTRICT_BY_SCOPES and not values.LRS_RESTRICT_BY_AUTHORITY:
            raise ConfigurationException(
                "LRS_RESTRICT_BY_AUTHORITY must be set to True if using "
                "LRS_RESTRICT_BY_SCOPES=True"
            )
        return values


settings = Settings()
