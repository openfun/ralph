"""Base HTTP backend for Ralph."""

import logging
from abc import ABC, abstractmethod
from typing import Iterable, Iterator, Union

logger = logging.getLogger(__name__)


class BaseHTTP(ABC):
    """Base HTTP backend interface."""

    name = "base"

    @abstractmethod
    def async_get_statements(
        self, target: str, chunk_size: Union[None, int] = None
    ) -> Iterator[dict]:
        """Yields records read from the HTTP response results."""

    @abstractmethod
    def async_post_statements(
        self,   
        target: str,
        data: Union[dict, Iterable[dict]],
        chunk_size: Union[None, int] = None
    ) -> int:
        """POST request to the HTTP server given an input endpoint."""
