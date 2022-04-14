"""Tests for Ralph base stream backend"""

from ralph.backends.stream.base import BaseStream


def test_backends_stream_base_abstract_interface_with_implemented_abstract_method():
    """Tests the interface mechanism with properly implemented abstract methods."""

    class GoodStream(BaseStream):
        """Correct implementation with required abstract methods."""

        name = "good"

        def stream(self, target):
            """Fakes the stream method."""

    GoodStream()

    assert GoodStream.name == "good"
