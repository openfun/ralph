"""Base Stream backend for Ralph."""

from abc import ABC, abstractmethod
from typing import BinaryIO

from ralph.conf import BaseSettingsConfig, core_settings
from pydantic_settings import BaseSettings


class BaseStreamBackendSettings(BaseSettings):
    """Data backend default configuration."""

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__STREAM__"
        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING


class BaseStreamBackend(ABC):
    """Base stream backend interface."""

    type = "stream"
    name = "base"
    settings_class = BaseStreamBackendSettings

    @abstractmethod
    def stream(self, target: BinaryIO) -> None:
        """Read records and stream them to target."""
