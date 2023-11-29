"""Websocket stream backend for Ralph."""

from typing import AsyncIterator, Dict, Optional, Union

import websockets
from pydantic import PositiveInt

from ralph.backends.data.base import (
    BaseAsyncDataBackend,
    BaseDataBackendSettings,
    BaseQuery,
    DataBackendStatus,
)
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException


class WSDataBackendSettings(BaseDataBackendSettings):
    """Websocket data backend default configuration.

    Attributes:
        URI (str): The URI to connect to.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__WS__"

    URI: Optional[str] = None


class AsyncWSDataBackend(BaseAsyncDataBackend[WSDataBackendSettings, BaseQuery]):
    """Websocket stream backend."""

    name = "async_ws"

    def __init__(self, settings: Optional[WSDataBackendSettings] = None):
        """Instantiate the async websocket data backend.

        Args:
            settings (WSDataBackendSettings or None): The websocket backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self._clients: Dict[str, websockets.WebSocketClientProtocol] = {}

    async def client(self, uri: str) -> websockets.WebSocketClientProtocol:
        """Create an websocket client for the provided `URI` if it doesn't exist."""
        if uri not in self._clients:
            try:
                self._clients[uri] = await websockets.connect(uri)
            except (websockets.WebSocketException, OSError, TimeoutError) as error:
                msg = "Failed open websocket connection for %s: %s"
                self.logger.error(msg, uri, error)
                raise BackendException(msg % (uri, error)) from error
        return self._clients[uri]

    async def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """
        try:
            client = await self.client(self.settings.URI)
            await client.close()
            del self._clients[self.settings.URI]
        except BackendException:
            return DataBackendStatus.ERROR
        return DataBackendStatus.OK

    async def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, BaseQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        prefetch: Optional[PositiveInt] = None,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[AsyncIterator[bytes], AsyncIterator[dict]]:
        """Read records matching the `query` in the `target` container and yield them.

        Args:
            query: (str or Query): Ignored.
            target (str or None): The target websocket URI to connect to.
                If `target` is `None`, it defaults to `settings.URI`.
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
        query: BaseQuery,  # noqa: ARG002
        target: Optional[str],
        chunk_size: int,  # noqa: ARG002
        ignore_errors: bool,  # noqa: ARG002
    ) -> AsyncIterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        uri = target if target else self.settings.URI
        client = await self.client(uri)
        count = 0
        try:
            while event := await client.recv():
                yield bytes(f"{event}\n", encoding=self.settings.LOCALE_ENCODING)
                count += 1
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.info("Read %s records with success", count)
        except (websockets.WebSocketException, RuntimeError) as error:
            msg = "Failed to receive message from websocket %s: %s"
            self.logger.error(msg, uri, error)
            raise BackendException(msg % (uri, error)) from error

    async def _read_dicts(
        self,
        query: BaseQuery,
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
        if not self._clients:
            self.logger.warning("No backend client to close.")
            return

        errors = {}
        for uri, client in self._clients.items():
            try:
                await client.close()
            except (websockets.WebSocketException, OSError, TimeoutError) as error:
                msg = "Failed to close websocket connection for %s: %s"
                self.logger.error(msg, uri, error)
                errors[uri] = error

        self._clients = {}
        if errors:
            msg = "Failed to close websocket connections: %s"
            raise BackendException(msg % errors)
