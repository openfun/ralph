"""Base LRS backend for Ralph."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterator, List, Optional

from pydantic import BaseModel

from ralph.backends.data.base import (
    BaseAsyncDataBackend,
    BaseDataBackend,
    BaseDataBackendSettings,
)
from ralph.backends.http.async_lrs import LRSStatementsQuery


class BaseLRSBackendSettings(BaseDataBackendSettings):
    """LRS backend default configuration."""


@dataclass
class StatementQueryResult:
    """Result of an LRS statements query."""

    statements: List[dict]
    pit_id: Optional[str]
    search_after: Optional[str]


class AgentParameters(BaseModel):
    """LRS query parameters for query on type Agent.

    NB: Agent refers to the data structure, NOT to the LRS query parameter.
    """

    mbox: Optional[str] = None
    mbox_sha1sum: Optional[str] = None
    openid: Optional[str] = None
    account__name: Optional[str] = None
    account__home_page: Optional[str] = None


class RalphStatementsQuery(LRSStatementsQuery):
    """Represents a dictionary of possible LRS query parameters."""

    agent: Optional[AgentParameters] = AgentParameters.construct()
    search_after: Optional[str] = None
    pit_id: Optional[str] = None
    authority: Optional[AgentParameters] = AgentParameters.construct()
    ignore_order: Optional[bool] = None


class BaseLRSBackend(BaseDataBackend):
    """Base LRS backend interface."""

    type = "lrs"
    settings_class = BaseLRSBackendSettings

    @abstractmethod
    def query_statements(self, params: RalphStatementsQuery) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""


class BaseAsyncLRSBackend(BaseAsyncDataBackend):
    """Base async LRS backend interface."""

    type = "lrs"
    settings_class = BaseLRSBackendSettings

    @abstractmethod
    async def query_statements(
        self, params: RalphStatementsQuery
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    async def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Return the list of matching statement IDs from the database."""
