"""Base database backend for Ralph."""

import functools
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, unique
from typing import BinaryIO, List, Literal, Optional, TextIO, Union
from uuid import UUID

from pydantic import ConfigDict, BaseModel

from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


class BaseQuery(BaseModel):
    """Base query model."""
    model_config = ConfigDict(extra="forbid")


@dataclass
class StatementQueryResult:
    """Represents a common interface for results of an LRS statements query."""

    statements: List[dict]
    pit_id: str
    search_after: str


@unique
class DatabaseStatus(Enum):
    """Database statuses."""

    OK = "ok"
    AWAY = "away"
    ERROR = "error"


@dataclass
class AgentParameters:
    """Dictionary of possible LRS query parameters for query on type Agent.

    NB: Agent refers to the data structure, NOT to the LRS query parameter.
    """

    mbox: Optional[str] = None
    mbox_sha1sum: Optional[str] = None
    openid: Optional[str] = None
    account__name: Optional[str] = None
    account__home_page: Optional[str] = None


@dataclass
class StatementParameters:
    """Represents a dictionary of possible LRS query parameters."""

    # pylint: disable=too-many-instance-attributes

    statementId: Optional[str] = None  # pylint: disable=invalid-name
    voidedStatementId: Optional[str] = None  # pylint: disable=invalid-name
    agent: Optional[AgentParameters] = None
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
    authority: Optional[AgentParameters] = None

    def __post_init__(self):
        """Perform additional conformity verifications on parameters."""
        # Initiate agent parameters for queries "agent" and "authority"
        for query_param in ["agent", "authority"]:
            # Transform to object if None (cannot be done with defaults)
            if self.__dict__[query_param] is None:
                self.__dict__[query_param] = AgentParameters()

            # Check that both `homePage` and `name` are provided if any are
            if (self.__dict__[query_param].account__name is not None) != (
                self.__dict__[query_param].account__home_page is not None
            ):
                raise BackendParameterException(
                    f"Invalid {query_param} parameters: homePage and name are "
                    "both required"
                )

            # Check that one or less Inverse Functional Identifier is provided
            if (
                sum(
                    x is not None
                    for x in [
                        self.__dict__[query_param].mbox,
                        self.__dict__[query_param].mbox_sha1sum,
                        self.__dict__[query_param].openid,
                        self.__dict__[query_param].account__name,
                    ]
                )
                > 1
            ):
                raise BackendParameterException(
                    f"Invalid {query_param} parameters: Only one identifier can be used"
                )


def enforce_query_checks(method):
    """Enforce query argument type checking for methods using it."""

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        """Wrap method execution."""
        query = kwargs.pop("query", None)
        self_ = args[0]

        return method(*args, query=self_.validate_query(query), **kwargs)

    return wrapper


class BaseDatabase(ABC):
    """Base database backend interface."""

    name = "base"
    query_model = BaseQuery

    def validate_query(self, query: BaseQuery = None):
        """Validate database query."""
        if query is None:
            query = self.query_model()

        if not isinstance(query, self.query_model):
            raise BackendParameterException(
                "'query' argument is expected to be a "
                f"{self.query_model().__class__.__name__} instance."
            )

        logger.debug("Query: %s", str(query))

        return query

    @abstractmethod
    def status(self) -> DatabaseStatus:
        """Implements database checks (e.g. connection, cluster status)."""

    @abstractmethod
    @enforce_query_checks
    def get(self, query: BaseQuery = None, chunk_size: int = 10):
        """Yields `chunk_size` records read from the database query results."""

    @abstractmethod
    def put(
        self,
        stream: Union[BinaryIO, TextIO],
        chunk_size: int = 10,
        ignore_errors: bool = False,
    ) -> int:
        """Writes `chunk_size` records from the `stream` to the database.

        Returns:
            int: The count of successfully written records.
        """

    @abstractmethod
    def query_statements(self, params: StatementParameters) -> StatementQueryResult:
        """Returns the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(self, ids: List[str]) -> List:
        """Returns the list of matching statement IDs from the database."""
