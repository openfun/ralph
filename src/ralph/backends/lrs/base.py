"""Base LRS backend for Ralph."""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    AsyncIterator,
    Iterator,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
)
from uuid import UUID

from pydantic import BaseModel, Field, NonNegativeInt
from pydantic_settings import SettingsConfigDict
from typing_extensions import Annotated

from ralph.backends.data.base import (
    BaseAsyncDataBackend,
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseQuery,
)
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.models.xapi.base.agents import BaseXapiAgent
from ralph.models.xapi.base.common import IRI
from ralph.models.xapi.base.groups import BaseXapiGroup


class BaseLRSBackendSettings(BaseDataBackendSettings):
    """LRS backend default configuration."""

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__"),
    }


@dataclass
class StatementQueryResult:
    """Result of an LRS statements query."""

    statements: List[dict]
    pit_id: Optional[str]
    search_after: Optional[str]


class LRSStatementsQuery(BaseQuery):
    """Pydantic model for LRS query on Statements resource query parameters.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#213-get-statements
    """

    statement_id: Annotated[Optional[str], Field(None, alias="statementId")]
    voided_statement_id: Annotated[
        Optional[str], Field(None, alias="voidedStatementId")
    ]
    agent: Optional[Union[BaseXapiAgent, BaseXapiGroup]] = None
    verb: Optional[IRI] = None
    activity: Optional[IRI] = None
    registration: Optional[UUID] = None
    related_activities: Optional[bool] = False
    related_agents: Optional[bool] = False
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: Optional[NonNegativeInt] = 0
    format: Optional[Literal["ids", "exact", "canonical"]] = "exact"
    attachments: Optional[bool] = False
    ascending: Optional[bool] = False


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

    agent: Optional[AgentParameters] = AgentParameters.model_construct()
    search_after: Optional[str] = None
    pit_id: Optional[str] = None
    authority: Optional[AgentParameters] = AgentParameters.model_construct()
    ignore_order: Optional[bool] = None


Settings = TypeVar("Settings", bound=BaseLRSBackendSettings)


class BaseLRSBackend(BaseDataBackend[Settings, Any]):
    """Base LRS backend interface."""

    @abstractmethod
    def query_statements(self, params: RalphStatementsQuery) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""


class BaseAsyncLRSBackend(BaseAsyncDataBackend[Settings, Any]):
    """Base async LRS backend interface."""

    @abstractmethod
    async def query_statements(
        self, params: RalphStatementsQuery
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    async def query_statements_by_ids(self, ids: List[str]) -> AsyncIterator[dict]:
        """Return the list of matching statement IDs from the database."""
