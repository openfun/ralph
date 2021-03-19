"""Tests for Ralph base storage backend"""

from ralph.backends.storage.base import BaseStorage


def test_backends_storage_base_abstract_interface_with_implemented_abstract_method():
    """Tests the interface mechanism with properly implemented abstract methods."""

    class GoodStorage(BaseStorage):
        """Correct implementation with required abstract methods."""

        name = "good"

        def list(self, details=False, new=False):
            """Fakes the list method."""

        def url(self, name):
            """Fakes the url method."""

        def read(self, name, chunk_size=0):
            """Fakes the read method."""

        def write(self, name, chunk_size=4096, overwrite=False):
            """Fakes the write method."""

    GoodStorage()

    assert GoodStorage.name == "good"
