"""Base storage backend for Ralph"""

from abc import ABC, abstractmethod


class BaseDatabase(ABC):
    """Base database backend interface"""

    name = "base"

    @abstractmethod
    def get(self, chunk_size=10):
        """Read chunk_size records and stream them to stdout"""

    @abstractmethod
    def put(self, chunk_size=10):
        """Write chunk_size records from stdin"""
