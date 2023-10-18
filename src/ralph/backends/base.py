"""Base ralph backend interface."""

from abc import ABC
from typing import Generic, Type, TypeVar, Union

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


Settings = TypeVar("Settings", bound=BaseBackendSettings)


class BaseBackend(Generic[Settings], ABC):
    """Base ralph backend class."""

    settings_class: Type[Settings]

    def __init_subclass__(cls, **kwargs):  # noqa: D105
        super().__init_subclass__(**kwargs)
        # pylint: disable=no-member
        # To let generic backends co-exist with previous approach.
        # Remove this if condition to force all backends to define generic parameters.
        if isinstance(cls.__orig_bases__[0].__args__[0], TypeVar):
            return
        cls.settings_class = cls.__orig_bases__[0].__args__[0]

    def __init__(self, settings: Union[Settings, None] = None):
        """Instantiate the backend.

        Args:
            settings (BaseBackendSettings or None): The backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings: Settings = settings if settings else self.settings_class()
