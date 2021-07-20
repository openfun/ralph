"""Base Stream backend for Ralph"""

from abc import ABC, abstractmethod


class BaseStream(ABC):
    """Base stream backend interface."""

    name = "base"

    @abstractmethod
    def stream(self):
        """Read records and stream them to stdout."""
