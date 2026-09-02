"""Elasticsearch LRS backend for Ralph."""

import logging
from typing import Iterator, List, Optional

from pydantic_settings import SettingsConfigDict

from ralph.backends.data.es import (
    ESDataBackend,
    ESDataBackendSettings,
    ESQuery,
    ESQueryPit,
)
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    BaseLRSBackendSettings,
    RalphStatementsQuery,
    StatementQueryResult,
)
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class ESLRSBackendSettings(BaseLRSBackendSettings, ESDataBackendSettings):
    """Elasticsearch LRS backend default configuration."""

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__ES__"),
    }


class ESLRSBackend(BaseLRSBackend[ESLRSBackendSettings], ESDataBackend):
    """Elasticsearch LRS backend implementation."""

    def query_statements(
        self, params: RalphStatementsQuery, target: Optional[str] = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        query = self.get_query(params=params)
        try:
            es_documents = self.read(
                query=query, target=target, chunk_size=params.limit
            )
            statements = [document["_source"] for document in es_documents]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

        return StatementQueryResult(
            statements=statements,
            pit_id=query.pit.id,
            search_after="|".join(query.search_after) if query.search_after else "",
        )

    def query_statements_by_ids(
        self, ids: List[str], target: Optional[str] = None
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        query = self.query_class(query={"terms": {"_id": ids}})
        try:
            es_response = self.read(query=query, target=target)
            yield from (document["_source"] for document in es_response)
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

    @staticmethod
    def get_query(params: RalphStatementsQuery) -> ESQuery:
        """Construct query from statement parameters."""
        es_query_filters = []

        if params.statement_id:
            es_query_filters += [{"term": {"_id": params.statement_id}}]

        ESLRSBackend._add_agent_filters(es_query_filters, params.agent, "actor")
        ESLRSBackend._add_agent_filters(es_query_filters, params.authority, "authority")

        if params.verb:
            es_query_filters += [{"term": {"verb.id.keyword": params.verb}}]

        if params.activity:
            es_query_filters += [
                {"term": {"object.id.keyword": params.activity}},
            ]

        if params.since:
            es_query_filters += [{"range": {"timestamp": {"gt": params.since}}}]

        if params.until:
            es_query_filters += [{"range": {"timestamp": {"lte": params.until}}}]

        es_query = {
            "pit": ESQueryPit.model_construct(id=params.pit_id),
            "size": params.limit,
            "sort": [{"timestamp": {"order": "asc" if params.ascending else "desc"}}],
        }
        if len(es_query_filters) > 0:
            es_query["query"] = {"bool": {"filter": es_query_filters}}

        if params.ignore_order:
            es_query["sort"] = "_shard_doc"

        if params.search_after:
            es_query["search_after"] = params.search_after.split("|")

        # Note: `params` fields are validated thus we skip their validation in ESQuery.
        logger.debug(es_query)
        return ESQuery.model_construct(**es_query)

    @staticmethod
    def _add_agent_filters(
        es_query_filters: list, agent_params: AgentParameters, target_field: str
    ) -> None:
        """Add filters relative to agents to `es_query_filters`."""

        def _get_agent_filters(_params: AgentParameters) -> dict | None:
            if not _params:
                return None

            if not isinstance(_params, dict):
                _params = _params.model_dump()

            if _params.get("mbox"):
                field = f"{target_field}.mbox.keyword"
                return {"term": {field: _params.get("mbox")}}
            elif _params.get("mbox_sha1sum"):
                field = f"{target_field}.mbox_sha1sum.keyword"
                return {"term": {field: _params.get("mbox_sha1sum")}}
            elif _params.get("openid"):
                field = f"{target_field}.openid.keyword"
                return {"term": {field: _params.get("openid")}}
            elif _params.get("account__name"):
                field_name = f"{target_field}.account.name.keyword"
                field_homepage = f"{target_field}.account.homePage.keyword"
                return {
                    "bool": {
                        "filter": [
                            {"term": {field_name: _params.get("account__name")}},
                            {
                                "term": {
                                    field_homepage: _params.get("account__home_page")
                                }
                            },
                        ]
                    }
                }
            return None

        if not agent_params:
            return
        elif not isinstance(agent_params, list):
            filters = _get_agent_filters(agent_params)
            if filters:
                es_query_filters += [filters]
        else:
            filters = [_get_agent_filters(params) for params in agent_params if params]
            es_query_filters += [{"bool": {"should": filters}}]
