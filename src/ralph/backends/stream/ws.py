"""Websocket stream backend for Ralph"""

import asyncio
import logging
from typing import BinaryIO

import websockets

from ralph.conf import settings

from .base import BaseStream

logger = logging.getLogger(__name__)


class WSStream(BaseStream):
    """Websocket stream backend."""

    name = "ws"

    def __init__(self, uri: str = settings.BACKENDS.STREAM.WS.URI):
        """Instantiates the websocket client.

        Args:
            uri (str): The URI to connect to.
        """

        self.uri = uri

    def stream(self, target: BinaryIO):
        """Streams websocket content to target."""
        # pylint: disable=no-member

        logger.debug("Streaming from websocket uri: %s", self.uri)

        async def _stream():
            async with websockets.connect(self.uri) as websocket:
                while event := await websocket.recv():
                    target.write(bytes(f"{event}" + "\n", encoding="utf-8"))

        asyncio.get_event_loop().run_until_complete(_stream())
