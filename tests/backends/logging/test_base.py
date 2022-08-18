"""Tests for Ralph base logging backend"""

from ralph.backends.logging.base import BaseLogging


def test_backends_logging_base_abstract_interface_with_implemented_abstract_method():
    """Tests the interface mechanism with properly implemented abstract methods."""

    class GoodLogging(BaseLogging):
        """Correct implementation with required abstract methods."""

        name = "good"

        def get(self, chunk_size=10):
            """Fakes the get method."""

        def send(self, chunk_size=10, ignore_errors=False):
            """Fakes the send method."""

    GoodLogging()

    assert GoodLogging.name == "good"
