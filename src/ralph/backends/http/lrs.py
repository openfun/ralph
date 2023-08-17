"""LRS HTTP backend for Ralph."""
import asyncio

from ralph.backends.http.async_lrs import AsyncLRSHTTPBackend


def _ensure_running_loop_uniqueness(func):
    """Raise an error when methods are used in a running asyncio events loop."""

    def wrap(*args, **kwargs):
        """Wrapper for decorator function."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return func(*args, **kwargs)
        if loop.is_running():
            raise RuntimeError(
                f"This event loop is already running. You must use "
                f"`AsyncLRSHTTPBackend.{func.__name__}` (instead of `LRSHTTPBackend."
                f"{func.__name__}`), or run this code outside the current"
                " event loop."
            )
        return func(*args, **kwargs)

    return wrap


class LRSHTTPBackend(AsyncLRSHTTPBackend):
    """LRS HTTP backend."""

    # pylint: disable=invalid-overridden-method

    name = "lrs"

    @_ensure_running_loop_uniqueness
    def status(self, *args, **kwargs):
        """HTTP backend check for server status."""
        return asyncio.get_event_loop().run_until_complete(
            super().status(*args, **kwargs)
        )

    @_ensure_running_loop_uniqueness
    def list(self, *args, **kwargs):
        """Raise error for unsuported `list` method."""
        return asyncio.get_event_loop().run_until_complete(
            super().list(*args, **kwargs)
        )

    @_ensure_running_loop_uniqueness
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

    @_ensure_running_loop_uniqueness
    def write(self, *args, **kwargs):
        """Write `data` records to the `target` endpoint and return their count.

        See AsyncLRSHTTP.write for more information.
        """
        return asyncio.get_event_loop().run_until_complete(
            super().write(*args, **kwargs)
        )
