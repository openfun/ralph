"""Websocket stream backend for Ralph."""

import logging
from typing import AsyncIterator, Optional, Union

import websockets
from pydantic import AnyUrl, PositiveInt
from pydantic_settings import SettingsConfigDict
from websockets.http import USER_AGENT

from ralph.backends.data.base import (
    BaseAsyncDataBackend,
    BaseDataBackendSettings,
    DataBackendStatus,
)
from ralph.conf import BASE_SETTINGS_CONFIG, ClientOptions
from ralph.exceptions import BackendException

logger = logging.getLogger(__name__)


class WSClientOptions(ClientOptions):
    """Client options for `websockets.connection`.

    For mode details, see the
    [websockets.connection documentation](https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html#websockets.client.connect)

    Attributes:
        close_timeout (float): Timeout for opening the connection in seconds.
        compression (str): Per-message compression (deflate) is activated by default.
            Setting it to `None` disables compression.
        max_size (int): Maximum size of incoming messages in bytes.
            Setting it to `None` disables the limit.
        max_queue (int): Maximum number of incoming messages in receive buffer.
            Setting it to `None` disables the limit.
        open_timeout (float): Timeout for opening the connection in seconds.
            Setting it to `None` disables the timeout.
        origin (str): Value of the `Origin` header, for servers that require it.
        ping_interval (float): Delay between keepalive pings in seconds.
            Setting it to `None` disables keepalive pings.
        ping_timeout (float): Timeout for keepalive pings in seconds.
            Setting it to `None` disables timeouts.
        read_limit (int): High-water mark of read buffer in bytes.
        user_agent_header (str): Value of  the `User-Agent` request header.
            It defaults to "Python/x.y.z websockets/X.Y".
            Setting it to `None` removes the header.
        write_limit (int): High-water mark of write buffer in bytes.
    """

    close_timeout: Optional[float] = None
    compression: Optional[str] = "deflate"
    max_size: Optional[int] = 2**20
    max_queue: Optional[int] = 2**5
    open_timeout: Optional[float] = 10
    origin: Optional[str] = None
    ping_interval: Optional[float] = 20
    ping_timeout: Optional[float] = 20
    read_limit: int = 2**16
    user_agent_header: Optional[str] = USER_AGENT
    write_limit: int = 2**16


class WSDataBackendSettings(BaseDataBackendSettings):
    """Websocket data backend default configuration.

    Attributes:
        CLIENT_OPTIONS (dict): A dictionary of valid options for the websocket client
            connection. See `WSClientOptions`.
        URI (str): The URI to connect to.
    """

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__DATA__WS__"),
    }

    CLIENT_OPTIONS: WSClientOptions = WSClientOptions()
    URI: AnyUrl


class AsyncWSDataBackend(BaseAsyncDataBackend[WSDataBackendSettings, str]):
    """Websocket stream backend."""

    name = "async_ws"

    def __init__(self, settings: Optional[WSDataBackendSettings] = None):
        """Instantiate the async websocket data backend.

        Args:
            settings (WSDataBackendSettings or None): The websocket backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self._client = None

    async def client(self) -> websockets.WebSocketClientProtocol:
        """Create a websocket client connected to `settings.URI` if it doesn't exist."""
        if not self._client:
            try:
                self._client = await websockets.connect(
                    str(self.settings.URI), **self.settings.CLIENT_OPTIONS.model_dump()
                )
            except (websockets.WebSocketException, OSError, TimeoutError) as error:
                msg = "Failed open websocket connection for %s: %s"
                logger.error(msg, self.settings.URI, error)
                raise BackendException(msg % (self.settings.URI, error)) from error
        return self._client

    async def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """
        try:
            client = await self.client()
            pong_waiter = await client.ping()
            await pong_waiter
        except BackendException:
            return DataBackendStatus.ERROR
        except (websockets.WebSocketException, RuntimeError) as error:
            logger.error("Failed to Ping %s: %s", self.settings.URI, error)
            return DataBackendStatus.AWAY
        return DataBackendStatus.OK

    async def read(  # noqa: PLR0913
        self,
        query: Optional[str] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        prefetch: Optional[PositiveInt] = None,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[AsyncIterator[bytes], AsyncIterator[dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query (str): Ignored.
            target (str or None): Ignored.
            chunk_size (int or None): Ignored.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
                If the records are dictionaries and `raw_output` is set to `True`, they
                are encoded as JSON.
                If the records are bytes and `raw_output` is set to `False`, they are
                decoded as JSON by line.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            prefetch (int): The number of records to prefetch (queue) while yielding.
                If `prefetch` is `None` it defaults to `1` - no records are prefetched.
            max_statements (int): The maximum number of statements to yield.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs or
                during encoding records and `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        statements = super().read(
            query,
            target,
            chunk_size,
            raw_output,
            ignore_errors,
            prefetch,
            max_statements,
        )
        async for statement in statements:
            yield statement

    async def _read_bytes(
        self,
        query: str,  # noqa: ARG002
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> AsyncIterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        if target or chunk_size:
            logger.warning("The `target` and `chunk_size` arguments are ignored")

        client = await self.client()
        count = 0
        try:
            while event := await client.recv():
                yield bytes(f"{event}\n", encoding=self.settings.LOCALE_ENCODING)
                count += 1
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Read %s records with success", count)
        except (websockets.WebSocketException, RuntimeError) as error:
            msg = "Failed to receive message from websocket %s: %s"
            logger.error(msg, self.settings.URI, error)
            raise BackendException(msg % (self.settings.URI, error)) from error

    async def _read_dicts(
        self,
        query: str,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
    ) -> AsyncIterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        statements = super()._read_dicts(query, target, chunk_size, ignore_errors)
        async for statement in statements:
            yield statement

    async def close(self) -> None:
        """Close the websocket client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            logger.warning("No backend client to close.")
            return

        client = await self.client()
        try:
            await client.close()
        except (websockets.WebSocketException, OSError, TimeoutError) as error:
            msg = "Failed to close websocket connection for %s: %s"
            logger.error(msg, self.settings.URI, error)
            raise BackendException(msg % (self.settings.URI, error)) from error
