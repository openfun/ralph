"""Base Stream backend for Ralph."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class BaseStream(ABC):
    """Base stream backend interface."""

    name = "base"

    @abstractmethod
    def stream(self, target: BinaryIO):
        """Read records and streams them to target."""
