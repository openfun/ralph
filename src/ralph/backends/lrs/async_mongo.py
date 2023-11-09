"""Async MongoDB LRS backend for Ralph."""


import logging
from typing import Iterator, List

from ralph.backends.data.async_mongo import AsyncMongoDataBackend
from ralph.backends.lrs.base import (
    BaseAsyncLRSBackend,
    RalphStatementsQuery,
    StatementQueryResult,
)
from ralph.backends.lrs.mongo import MongoLRSBackend, MongoLRSBackendSettings
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class AsyncMongoLRSBackend(
    BaseAsyncLRSBackend[MongoLRSBackendSettings], AsyncMongoDataBackend
):
    """Async MongoDB LRS backend implementation."""

    async def query_statements(
        self, params: RalphStatementsQuery
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        query = MongoLRSBackend.get_query(params)
        try:
            mongo_response = [
                document
                async for document in self.read(query=query, chunk_size=params.limit)
            ]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from async MongoDB")
            raise error

        search_after = None
        if mongo_response:
            search_after = mongo_response[-1]["_id"]

        return StatementQueryResult(
            statements=[document["_source"] for document in mongo_response],
            pit_id=None,
            search_after=search_after,
        )

    async def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        try:
            async for document in self.read(
                query={"filter": {"_source.id": {"$in": ids}}}
            ):
                yield document["_source"]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from MongoDB")
            raise error
