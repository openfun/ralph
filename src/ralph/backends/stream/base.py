"""Base Stream backend for Ralph."""

from abc import abstractmethod
from typing import BinaryIO

from ralph.backends.base import (
    BaseBackend,
    BaseBackendSettings,
    BaseBackendSettingsConfig,
)


class BaseStreamBackendSettings(BaseBackendSettings):
    """Data backend default configuration."""

    class Config(BaseBackendSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__STREAM__"


class BaseStreamBackend(BaseBackend):
    """Base stream backend interface."""

    type = "stream"
    name = "base"
    settings_class = BaseStreamBackendSettings

    @abstractmethod
    def stream(self, target: BinaryIO):
        """Read records and stream them to target."""
