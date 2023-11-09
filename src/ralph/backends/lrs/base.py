"""Base LRS backend for Ralph."""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, NonNegativeInt

from ralph.backends.data.base import (
    BaseAsyncDataBackend,
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseSettingsConfig,
)
from ralph.models.xapi.base.agents import BaseXapiAgent
from ralph.models.xapi.base.common import IRI
from ralph.models.xapi.base.groups import BaseXapiGroup


class BaseLRSBackendSettings(BaseDataBackendSettings):
    """LRS backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__LRS__"


@dataclass
class StatementQueryResult:
    """Result of an LRS statements query."""

    statements: List[dict]
    pit_id: Optional[str]
    search_after: Optional[str]


class LRSStatementsQuery(BaseModel):
    """Base pydantic model for LRS query on Statements resource query parameters.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#213-get-statements
    """

    statement_id: Optional[str] = Field(None, alias="statementId")
    voided_statement_id: Optional[str] = Field(None, alias="voidedStatementId")
    agent: Optional[Union[BaseXapiAgent, BaseXapiGroup]]
    verb: Optional[IRI]
    activity: Optional[IRI]
    registration: Optional[UUID]
    related_activities: Optional[bool] = False
    related_agents: Optional[bool] = False
    since: Optional[datetime]
    until: Optional[datetime]
    limit: Optional[NonNegativeInt] = 0
    format: Optional[Literal["ids", "exact", "canonical"]] = "exact"
    attachments: Optional[bool] = False
    ascending: Optional[bool] = False


class AgentParameters(BaseModel):
    """LRS query parameters for query on type Agent.

    NB: Agent refers to the data structure, NOT to the LRS query parameter.
    """

    mbox: Optional[str]
    mbox_sha1sum: Optional[str]
    openid: Optional[str]
    account__name: Optional[str]
    account__home_page: Optional[str]


class RalphStatementsQuery(LRSStatementsQuery):
    """Represents a dictionary of possible LRS query parameters."""

    agent: Optional[AgentParameters] = AgentParameters.construct()
    search_after: Optional[str]
    pit_id: Optional[str]
    authority: Optional[AgentParameters] = AgentParameters.construct()
    ignore_order: Optional[bool]


class BaseLRSBackend(BaseDataBackend):
    """Base LRS backend interface."""

    settings_class = BaseLRSBackendSettings

    @abstractmethod
    def query_statements(self, params: RalphStatementsQuery) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""


class BaseAsyncLRSBackend(BaseAsyncDataBackend):
    """Base async LRS backend interface."""

    settings_class = BaseLRSBackendSettings

    @abstractmethod
    async def query_statements(
        self, params: RalphStatementsQuery
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    async def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Return the list of matching statement IDs from the database."""
