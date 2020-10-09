"""Tests for Ralph base storage backend"""

from ralph.backends.storage.base import BaseStorage


def test_abstract_interface_with_implemented_abstract_method():
    """Test interface mechanism with properly implemented abstract methods"""

    class GoodStorage(BaseStorage):
        """Correct implementation with required abstract methods"""

        name = "good"

        def list(self, details=False, new=False):
            """Fake list"""

        def url(self, name):
            """Fake url"""

        def read(self, name, chunk_size=0):
            """Fake read"""

        def write(self, name, content):
            """Fake write"""

    GoodStorage()

    assert GoodStorage.name == "good"
