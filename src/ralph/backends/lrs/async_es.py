"""Asynchronous Elasticsearch LRS backend for Ralph."""

from typing import Iterator, List

from ralph.backends.data.async_es import AsyncESDataBackend
from ralph.backends.lrs.base import (
    BaseAsyncLRSBackend,
    RalphStatementsQuery,
    StatementQueryResult,
)
from ralph.backends.lrs.es import ESLRSBackend, ESLRSBackendSettings
from ralph.exceptions import BackendException, BackendParameterException


class AsyncESLRSBackend(BaseAsyncLRSBackend[ESLRSBackendSettings], AsyncESDataBackend):
    """Asynchronous Elasticsearch LRS backend implementation."""

    async def query_statements(
        self, params: RalphStatementsQuery
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        query = ESLRSBackend.get_query(params=params)
        try:
            statements = [
                document["_source"]
                async for document in self.read(query=query, chunk_size=params.limit)
            ]
        except (BackendException, BackendParameterException) as error:
            self.logger.error("Failed to read from Elasticsearch")
            raise error

        return StatementQueryResult(
            statements=statements,
            pit_id=query.pit.id,
            search_after="|".join(query.search_after) if query.search_after else "",
        )

    async def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        try:
            async for document in self.read(query={"query": {"terms": {"_id": ids}}}):
                yield document["_source"]
        except (BackendException, BackendParameterException) as error:
            self.logger.error("Failed to read from Elasticsearch")
            raise error
