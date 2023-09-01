"""Base database backend for Ralph."""

import functools
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from typing import BinaryIO, List, Optional, TextIO, Union

from pydantic import BaseModel

from ralph.backends.http.async_lrs import LRSStatementsQuery
from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


class BaseQuery(BaseModel):
    """Base query model."""

    class Config:
        """Base query model configuration."""

        extra = "forbid"


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


class AgentParameters(BaseModel):
    """Dictionary of possible LRS query parameters for query on type Agent.

    NB: Agent refers to the data structure, NOT to the LRS query parameter.
    """

    mbox: Optional[str]
    mbox_sha1sum: Optional[str]
    openid: Optional[str]
    account__name: Optional[str]
    account__home_page: Optional[str]


class RalphStatementsQuery(LRSStatementsQuery):
    """Represents a dictionary of possible LRS query parameters."""

    # pylint: disable=too-many-instance-attributes

    agent: Optional[AgentParameters] = AgentParameters.construct()
    search_after: Optional[str]
    pit_id: Optional[str]
    authority: Optional[AgentParameters] = AgentParameters.construct()

    def __post_init__(self):
        """Perform additional conformity verifications on parameters."""
        # Initiate agent parameters for queries "agent" and "authority"
        for query_param in ["agent", "authority"]:
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
    def query_statements(self, params: RalphStatementsQuery) -> StatementQueryResult:
        """Returns the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(self, ids: List[str]) -> List:
        """Returns the list of matching statement IDs from the database."""
