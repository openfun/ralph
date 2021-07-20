"""Websocket stream backend for Ralph"""

import asyncio
import logging
import sys

import websockets

from .base import BaseStream

logger = logging.getLogger(__name__)


class WSStream(BaseStream):
    """Websocket stream backend."""

    name = "ws"

    def __init__(self, uri: str):
        """Instantiate the websocket client.

        uri: the URI to connect to
        """

        self.uri = uri

    def stream(self):
        """Stream websocket content to stdout."""
        # pylint: disable=no-member

        logger.debug("Streaming from websocket uri: %s", self.uri)

        async def _stream():
            async with websockets.connect(self.uri) as websocket:
                while event := await websocket.recv():
                    sys.stdout.buffer.write(bytes(f"{event}" + "\n", encoding="utf-8"))

        asyncio.get_event_loop().run_until_complete(_stream())
