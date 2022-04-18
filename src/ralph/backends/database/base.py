"""Base storage backend for Ralph"""

from abc import ABC, abstractmethod
from typing import BinaryIO, TextIO, Union


class BaseDatabase(ABC):
    """Base database backend interface."""

    name = "base"

    @abstractmethod
    def get(self, chunk_size: int = 10):
        """Reads `chunk_size` records from the database and yields them."""

    @abstractmethod
    def put(
        self,
        stream: Union[BinaryIO, TextIO],
        chunk_size: int = 10,
        ignore_errors: bool = False,
    ):
        """Writes `chunk_size` records from the `stream` to the database."""
