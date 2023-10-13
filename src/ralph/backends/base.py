"""Base ralph backend interface."""

from abc import ABC
from typing import Union

from pydantic import BaseSettings

from ralph.conf import BaseSettingsConfig, core_settings


class BaseBackendSettingsConfig(BaseSettingsConfig):
    """Base backend pydantic settings configuration."""

    env_file = ".env"
    env_file_encoding = core_settings.LOCALE_ENCODING


class BaseBackendSettings(BaseSettings):
    """Base backend default configuration."""

    class Config(BaseBackendSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__"


class BaseBackend(ABC):
    """Base ralph backend class."""

    settings_class = BaseBackendSettings
    settings: settings_class

    def __init__(self, settings: Union[settings_class, None] = None):
        """Instantiate the backend.

        Args:
            settings (BaseBackendSettings or None): The backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings = settings if settings else self.settings_class()
