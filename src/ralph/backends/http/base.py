"""Base HTTP backend for Ralph."""

import logging
from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import Iterator, List, Optional, Union

from pydantic import BaseSettings
from pydantic.types import PositiveInt

from ralph.conf import BaseSettingsConfig, core_settings

logger = logging.getLogger(__name__)


class BaseHTTPBackendSettings(BaseSettings):
    """Data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__HTTP__"
        env_file = ".env"
        env_file_encoding = core_settings.LOCALE_ENCODING


@unique
class HTTPBackendStatus(Enum):
    """HTTP backend statuses."""

    OK = "ok"
    AWAY = "away"
    ERROR = "error"


class OperationType(Enum):
    """Data backend operation types.

    Attributes:
        INDEX (str): creates a new record with a specific ID.
        CREATE (str): creates a new record without a specific ID.
        DELETE (str): deletes an existing record.
        UPDATE (str): updates or overwrites an existing record.
        APPEND (str): creates or appends data to an existing record.
    """

    INDEX = "index"
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    APPEND = "append"


class BaseHTTPBackend(ABC):
    """Base HTTP backend interface."""

    name = "base"
    query = None

    @abstractmethod
    async def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List containers in the data backend. E.g., collections, files, indexes."""

    @abstractmethod
    async def status(self) -> HTTPBackendStatus:
        """Implement HTTP backend check for server status."""

    @abstractmethod
    async def read(  # noqa: PLR0913
        self,
        query: Optional[str] = None,
        target: Optional[str] = None,
        chunk_size: Optional[PositiveInt] = 500,
        raw_output: bool = False,
        ignore_errors: bool = False,
        greedy: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Iterator[Union[bytes, dict]]:
        """Yield records read from the HTTP response results."""

    @abstractmethod
    async def write(  # noqa: PLR0913
        self,
        data: Union[List[bytes], List[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[PositiveInt] = 500,
        ignore_errors: bool = False,
        operation_type: Optional[OperationType] = None,
        simultaneous: bool = False,
        max_num_simultaneous: Optional[int] = None,
    ) -> int:
        """Write statements into the HTTP server given an input endpoint."""
