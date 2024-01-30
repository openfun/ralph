"""Asynchronous Elasticsearch LRS backend for Ralph."""

import logging
from typing import AsyncIterator, List, Optional

from ralph.backends.data.async_es import AsyncESDataBackend
from ralph.backends.lrs.base import (
    BaseAsyncLRSBackend,
    RalphStatementsQuery,
    StatementQueryResult,
)
from ralph.backends.lrs.es import ESLRSBackend, ESLRSBackendSettings
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class AsyncESLRSBackend(BaseAsyncLRSBackend[ESLRSBackendSettings], AsyncESDataBackend):
    """Asynchronous Elasticsearch LRS backend implementation."""

    async def query_statements(
        self, params: RalphStatementsQuery, target: Optional[str] = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        query = ESLRSBackend.get_query(params=params)
        try:
            statements = [
                document["_source"]
                async for document in self.read(
                    query=query, target=target, chunk_size=params.limit
                )
            ]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

        return StatementQueryResult(
            statements=statements,
            pit_id=query.pit.id,
            search_after="|".join(query.search_after) if query.search_after else "",
        )

    async def query_statements_by_ids(
        self, ids: List[str], target: Optional[str] = None
    ) -> AsyncIterator[dict]:
        """Yield statements with matching ids from the backend."""
        query = self.query_class(query={"terms": {"_id": ids}})
        try:
            async for document in self.read(query=query, target=target):
                yield document["_source"]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error
