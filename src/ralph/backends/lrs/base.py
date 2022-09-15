"""Base data backend for Ralph"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from ralph.backends.data.base import BaseDataBackend


@dataclass
class StatementQueryResult:
    """Represents a common interface for results of an LRS statements query."""

    statements: list[dict]
    pit_id: str
    search_after: str


@dataclass
class StatementParameters:
    """Represents a dictionary of possible LRS query parameters."""

    # pylint: disable=too-many-instance-attributes

    statementId: Optional[str] = None  # pylint: disable=invalid-name
    voidedStatementId: Optional[str] = None  # pylint: disable=invalid-name
    agent: Optional[str] = None
    verb: Optional[str] = None
    activity: Optional[str] = None
    registration: Optional[UUID] = None
    related_activities: Optional[bool] = False
    related_agents: Optional[bool] = False
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: Optional[int] = None
    format: Optional[Literal["ids", "exact", "canonical"]] = "exact"
    attachments: Optional[bool] = False
    ascending: Optional[bool] = False
    search_after: Optional[str] = None
    pit_id: Optional[str] = None


class BaseLRSBackend(BaseDataBackend):
    """Base LRS backend interface."""

    @abstractmethod
    def query_statements(self, params: StatementParameters) -> StatementQueryResult:
        """Returns the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(self, ids: list[str]) -> list:
        """Returns the list of matching statement IDs from the database."""
