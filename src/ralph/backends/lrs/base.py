"""Base LRS backend for Ralph."""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel

from ralph.backends.data.base import BaseDataBackend, BaseDataBackendSettings


class BaseLRSBackendSettings(BaseDataBackendSettings):
    """LRS backend default configuration."""


@dataclass
class StatementQueryResult:
    """Result of an LRS statements query."""

    statements: List[dict]
    pit_id: str
    search_after: str


class AgentParameters(BaseModel):
    """LRS query parameters for query on type Agent.

    NB: Agent refers to the data structure, NOT to the LRS query parameter.
    """

    mbox: Optional[str]
    mbox_sha1sum: Optional[str]
    openid: Optional[str]
    account__name: Optional[str]
    account__home_page: Optional[str]


class StatementParameters(BaseModel):
    """LRS statements query parameters."""

    # pylint: disable=too-many-instance-attributes

    statementId: Optional[str]  # pylint: disable=invalid-name
    voidedStatementId: Optional[str]  # pylint: disable=invalid-name
    agent: Optional[AgentParameters]
    verb: Optional[str]
    activity: Optional[str]
    registration: Optional[UUID]
    related_activities: Optional[bool]
    related_agents: Optional[bool]
    since: Optional[datetime]
    until: Optional[datetime]
    limit: Optional[int]
    format: Optional[Literal["ids", "exact", "canonical"]] = "exact"
    attachments: Optional[bool]
    ascending: Optional[bool]
    search_after: Optional[str]
    pit_id: Optional[str]
    authority: Optional[AgentParameters]
    ignore_order: Optional[bool]


class BaseLRSBackend(BaseDataBackend):
    """Base LRS backend interface."""

    settings_class = BaseLRSBackendSettings

    @abstractmethod
    def query_statements(self, params: StatementParameters) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
