"""Base storage backend for Ralph"""

from abc import ABC, abstractmethod
from typing import Iterable


class BaseDatabase(ABC):
    """Base database backend interface."""

    name = "base"

    @abstractmethod
    def get(self, chunk_size=10):
        """Reads `chunk_size` records from the database and yields them."""

    @abstractmethod
    def put(self, stream: Iterable, chunk_size=10, ignore_errors=False):
        """Writes `chunk_size` records from the `stream` to the database."""
