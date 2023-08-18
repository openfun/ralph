"""Base Stream backend for Ralph."""

from abc import ABC, abstractmethod
from typing import BinaryIO

from pydantic import BaseSettings

from ralph.conf import BaseSettingsConfig, core_settings


class BaseStreamBackendSettings(BaseSettings):
    """Data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__STREAM__"
        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING


class BaseStreamBackend(ABC):
    """Base stream backend interface."""

    name = "base"
    settings_class = BaseStreamBackendSettings

    @abstractmethod
    def stream(self, target: BinaryIO):
        """Read records and stream them to target."""
