"""Websocket stream backend for Ralph."""

import asyncio
import logging
from typing import BinaryIO

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

    URI: str = None


class WSStreamBackend(BaseStreamBackend[WSStreamBackendSettings]):
    """Websocket stream backend."""

    name = "ws"

    def stream(self, target: BinaryIO):
        """Stream websocket content to target."""
        # pylint: disable=no-member

        logger.debug("Streaming from websocket uri: %s", self.settings.URI)

        async def _stream():
            async with websockets.connect(self.settings.URI) as websocket:
                while event := await websocket.recv():
                    target.write(bytes(f"{event}" + "\n", encoding="utf-8"))

        asyncio.get_event_loop().run_until_complete(_stream())
