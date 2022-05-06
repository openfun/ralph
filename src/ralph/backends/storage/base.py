"""Base storage backend for Ralph"""

from abc import ABC, abstractmethod
from typing import Iterable


class BaseStorage(ABC):
    """Base storage backend interface."""

    name = "base"

    @abstractmethod
    def list(self, details=False, new=False):
        """Lists files in the storage backend."""

    @abstractmethod
    def url(self, name):
        """Gets `name` file absolute URL."""

    @abstractmethod
    def read(self, name, chunk_size: int = 4096):
        """Reads `name` file and yields its content by chunks of a given size."""

    @abstractmethod
    def write(self, stream: Iterable, name, overwrite=False):
        """Writes content to the `name` target."""
