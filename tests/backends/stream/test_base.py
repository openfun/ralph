"""Tests for Ralph base stream backend."""

from ralph.backends.stream.base import BaseStreamBackend


def test_backends_stream_base_abstract_interface_with_implemented_abstract_method():
    """Test the interface mechanism with properly implemented abstract methods."""

    class GoodStream(BaseStreamBackend):
        """Correct implementation with required abstract methods."""

        name = "good"

        def stream(self, target):
            """Fake the stream method."""

    GoodStream()

    assert GoodStream.name == "good"
