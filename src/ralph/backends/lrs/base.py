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

from pydantic import AfterValidator, BaseModel, Field, NonNegativeInt
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
    pit_id: Optional[str] = None
    search_after: Optional[str] = None


def validate_iso_datetime_str(value: Union[str, datetime]) -> datetime:
    """Value is expected to be an ISO 8601 date time string.

    Note that we also accept datetime python instance that will be converted
    to an ISO 8601 date time string.
    """
    if not isinstance(value, (str, datetime)):
        raise TypeError("a string or datetime is required")

    if isinstance(value, datetime):
        return value.isoformat()

    # Validate iso-string
    try:
        datetime.fromisoformat(value)
    except ValueError as err:
        raise ValueError("invalid ISO 8601 date time string") from err


IsoDatetimeStr = Annotated[
    Union[str, datetime], AfterValidator(validate_iso_datetime_str)
]


class LRSStatementsQuery(BaseQuery):
    """Pydantic model for LRS query on Statements resource query parameters.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#213-get-statements
    """

    statement_id: Annotated[Optional[str], Field(alias="statementId")] = None
    voided_statement_id: Annotated[Optional[str], Field(alias="voidedStatementId")] = (
        None
    )
    agent: Optional[Union[BaseXapiAgent, BaseXapiGroup]] = None
    verb: Optional[IRI] = None
    activity: Optional[IRI] = None
    registration: Optional[UUID] = None
    related_activities: Optional[bool] = False
    related_agents: Optional[bool] = False
    since: Optional[IsoDatetimeStr] = None
    until: Optional[IsoDatetimeStr] = None
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
    def query_statements(
        self, params: RalphStatementsQuery, target: Optional[str] = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(
        self, ids: List[str], target: Optional[str] = None
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""


class BaseAsyncLRSBackend(BaseAsyncDataBackend[Settings, Any]):
    """Base async LRS backend interface."""

    @abstractmethod
    async def query_statements(
        self, params: RalphStatementsQuery, target: Optional[str] = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    async def query_statements_by_ids(
        self, ids: List[str], target: Optional[str] = None
    ) -> AsyncIterator[dict]:
        """Return the list of matching statement IDs from the database."""
