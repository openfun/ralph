"""A module containing valid Ralph Backends."""

from ralph.backends.data.async_ws import AsyncWSDataBackend  # noqa: F401
from ralph.backends.data.fs import FSDataBackend  # noqa: F401
from ralph.backends.lrs.fs import FSLRSBackend


class TestBackend(FSLRSBackend):
    """Test Backend to check entry point discovery."""

    name = "TestBackend"


class TestIgnoredBackend(FSLRSBackend):
    """Test Backend to check ignored entry point discovery."""

    name = "TestIgnoredBackend"
