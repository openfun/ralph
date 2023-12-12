"""MongoDB LRS backend for Ralph."""

import logging
from typing import Iterator, List

from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING

from ralph.backends.data.mongo import (
    MongoDataBackend,
    MongoDataBackendSettings,
    MongoQuery,
)
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    BaseLRSBackendSettings,
    RalphStatementsQuery,
    StatementQueryResult,
)
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class MongoLRSBackendSettings(BaseLRSBackendSettings, MongoDataBackendSettings):
    """MongoDB LRS backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__LRS__MONGO__"


class MongoLRSBackend(BaseLRSBackend[MongoLRSBackendSettings], MongoDataBackend):
    """MongoDB LRS backend."""

    def query_statements(self, params: RalphStatementsQuery) -> StatementQueryResult:
        """Return the results of a statements query using xAPI parameters."""
        query = self.get_query(params)
        try:
            mongo_response = list(self.read(query=query, chunk_size=params.limit))
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from MongoDB")
            raise error

        search_after = None
        if mongo_response:
            search_after = mongo_response[-1]["_id"]

        return StatementQueryResult(
            statements=[document["_source"] for document in mongo_response],
            pit_id=None,
            search_after=search_after,
        )

    def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        query = self.query_class(filter={"_source.id": {"$in": ids}})
        try:
            mongo_response = self.read(query=query)
            yield from (document["_source"] for document in mongo_response)
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from MongoDB")
            raise error

    @staticmethod
    def get_query(params: RalphStatementsQuery) -> MongoQuery:
        """Construct query from statement parameters."""
        mongo_query_filters = {}

        if params.statement_id:
            mongo_query_filters.update({"_source.id": params.statement_id})

        MongoLRSBackend._add_agent_filters(mongo_query_filters, params.agent, "actor")
        MongoLRSBackend._add_agent_filters(
            mongo_query_filters, params.authority, "authority"
        )

        if params.verb:
            mongo_query_filters.update({"_source.verb.id": params.verb})

        if params.activity:
            mongo_query_filters.update(
                {
                    "_source.object.objectType": "Activity",
                    "_source.object.id": params.activity,
                },
            )

        if params.since:
            mongo_query_filters.update({"_source.timestamp": {"$gt": params.since}})

        if params.until:
            if not params.since:
                mongo_query_filters["_source.timestamp"] = {}
            mongo_query_filters["_source.timestamp"].update({"$lte": params.until})

        if params.search_after:
            search_order = "$gt" if params.ascending else "$lt"
            mongo_query_filters.update(
                {"_id": {search_order: ObjectId(params.search_after)}}
            )

        mongo_sort_order = ASCENDING if params.ascending else DESCENDING
        mongo_query_sort = [
            ("_source.timestamp", mongo_sort_order),
            ("_id", mongo_sort_order),
        ]

        # Note: `params` fields are validated thus we skip MongoQuery validation.
        return MongoQuery.construct(
            filter=mongo_query_filters, limit=params.limit, sort=mongo_query_sort
        )

    @staticmethod
    def _add_agent_filters(
        mongo_query_filters: dict, agent_params: AgentParameters, target_field: str
    ) -> None:
        """Add filters relative to agents to mongo_query_filters.

        Args:
            mongo_query_filters (dict): Filters passed to MongoDB query.
            agent_params (AgentParameters): Agent query parameters to search for.
            target_field (str): The target agent field name to perform the search.
        """
        if not agent_params:
            return

        if not isinstance(agent_params, dict):
            agent_params = agent_params.dict()

        if agent_params.get("mbox"):
            key = f"_source.{target_field}.mbox"
            mongo_query_filters.update({key: agent_params.get("mbox")})

        if agent_params.get("mbox_sha1sum"):
            key = f"_source.{target_field}.mbox_sha1sum"
            mongo_query_filters.update({key: agent_params.get("mbox_sha1sum")})

        if agent_params.get("openid"):
            key = f"_source.{target_field}.openid"
            mongo_query_filters.update({key: agent_params.get("openid")})

        if agent_params.get("account__name"):
            key = f"_source.{target_field}.account.name"
            mongo_query_filters.update({key: agent_params.get("account__name")})
            key = f"_source.{target_field}.account.homePage"
            mongo_query_filters.update({key: agent_params.get("account__home_page")})
