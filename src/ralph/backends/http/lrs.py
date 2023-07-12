"""LRS HTTP backend for Ralph."""
import asyncio

from ralph.backends.http.async_lrs import AsyncLRSHTTP


class LRSHTTP(AsyncLRSHTTP):
    """LRS HTTP backend."""

    # pylint: disable=invalid-overridden-method

    name = "lrs"

    def status(self, *args, **kwargs):
        """HTTP backend check for server status."""
        return asyncio.get_event_loop().run_until_complete(
            super().status(*args, **kwargs)
        )

    def list(self, *args, **kwargs):
        """Raise error for unsuported `list` method."""
        return asyncio.get_event_loop().run_until_complete(
            super().list(*args, **kwargs)
        )

    def read(self, *args, **kwargs):
        """Get statements from LRS `target` endpoint.

        See AsyncLRSHTTP.read for more information.
        """
        async_statements_gen = super().read(*args, **kwargs)
        loop = asyncio.get_event_loop()
        try:
            while True:
                yield loop.run_until_complete(async_statements_gen.__anext__())
        except StopAsyncIteration:
            pass

    def write(self, *args, **kwargs):
        """Write `data` records to the `target` endpoint and return their count.

        See AsyncLRSHTTP.write for more information.
        """
        return asyncio.get_event_loop().run_until_complete(
            super().write(*args, **kwargs)
        )
