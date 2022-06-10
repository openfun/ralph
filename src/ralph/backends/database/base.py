"""Base storage backend for Ralph"""

import functools
import logging
from abc import ABC, abstractmethod
from typing import BinaryIO, TextIO, Union

from pydantic import BaseModel

from ralph.exceptions import BackendParameterException

logger = logging.getLogger(__name__)


class BaseQuery(BaseModel):
    """Base query model"""

    class Config:
        """Base query model configuration."""

        extra = "forbid"


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
        """Validate database query"""

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
    @enforce_query_checks
    def get(self, query: BaseQuery = None, chunk_size: int = 10):
        """Reads `chunk_size` records from the database query results and yields
        them.
        """

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
