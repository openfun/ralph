"""Base Stream backend for Ralph."""

from abc import abstractmethod
from typing import BinaryIO, TypeVar

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


Settings = TypeVar("Settings", bound=BaseStreamBackendSettings)


class BaseStreamBackend(BaseBackend[Settings]):
    """Base stream backend interface."""

    type = "stream"
    name = "base"

    @abstractmethod
    def stream(self, target: BinaryIO):
        """Read records and stream them to target."""
