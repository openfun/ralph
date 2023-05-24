"""Websocket stream backend for Ralph."""

import asyncio
import logging
from typing import BinaryIO, Optional

import websockets

from ralph.conf import BaseSettingsConfig

from .base import BaseStreamBackend, BaseStreamBackendSettings

logger = logging.getLogger(__name__)


class WSStreamBackendSettings(BaseStreamBackendSettings):
    """Websocket stream backend default configuration.

    Attributes:
        URI (str): The URI to connect to.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__STREAM__WS__"

    URI: Optional[str] = None


class WSStreamBackend(BaseStreamBackend):
    """Websocket stream backend."""

    name = "ws"
    settings_class = WSStreamBackendSettings

    def __init__(self, settings: Optional[WSStreamBackendSettings] = None):
        """Instantiate the websocket client.

        Args:
            settings (WSStreamBackendSettings or None): The stream backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings = settings if settings else self.settings_class()

    def stream(self, target: BinaryIO) -> None:
        """Stream websocket content to target."""
        # pylint: disable=no-member

        logger.debug("Streaming from websocket uri: %s", self.settings.URI)

        async def _stream() -> None:
            async with websockets.connect(self.settings.URI) as websocket:
                while event := await websocket.recv():
                    target.write(bytes(f"{event}" + "\n", encoding="utf-8"))

        asyncio.get_event_loop().run_until_complete(_stream())
