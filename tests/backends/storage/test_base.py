"""Tests for Ralph base storage backend."""

from ralph.backends.storage.base import BaseStorage


def test_backends_storage_base_abstract_interface_with_implemented_abstract_method():
    """Test the interface mechanism with properly implemented abstract methods."""

    class GoodStorage(BaseStorage):
        """Correct implementation with required abstract methods."""

        name = "good"

        def list(self, details=False, new=False):
            """Fake the list method."""

        def url(self, name):
            """Fake the url method."""

        def read(self, name, chunk_size=0):
            """Fake the read method."""

        def write(self, stream, name, overwrite=False):
            """Fake the write method."""

    GoodStorage()

    assert GoodStorage.name == "good"
