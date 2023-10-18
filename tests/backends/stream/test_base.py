"""Tests for Ralph base stream backend."""

from ralph.backends.stream.base import BaseStreamBackend, BaseStreamBackendSettings


def test_backends_stream_base_abstract_interface_with_implemented_abstract_method():
    """Test the interface mechanism with properly implemented abstract methods."""

    class GoodStream(BaseStreamBackend[BaseStreamBackendSettings]):
        """Correct implementation with required abstract methods."""

        name = "good"

        def stream(self, target):
            """Fakes the stream method."""

    GoodStream()

    assert GoodStream.name == "good"
