"""Base logging backend for Ralph"""

from abc import ABC, abstractmethod


class BaseLogging(ABC):
    """Base logging backend interface."""

    name = "base"

    @abstractmethod
    def get(self, chunk_size=10):
        """Read chunk_size records and stream them to stdout."""

    @abstractmethod
    def send(self, chunk_size=10, ignore_errors=False):
        """Write chunk_size records from stdin."""
