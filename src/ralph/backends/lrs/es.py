"""Elasticsearch LRS backend for Ralph."""

import logging
from typing import Iterator, List, Optional, Union

from pydantic_settings import SettingsConfigDict

from ralph.backends.data.es import (
    ESDataBackend,
    ESDataBackendSettings,
    ESQuery,
    ESQueryPit,
)
from ralph.backends.lrs.base import (
    RELATED_AGENTS_FIELDS,
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

        if params.related_agents:
            ESLRSBackend._add_related_agent_filters(es_query_filters, params.agent)
        else:
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
        return ESQuery.model_construct(**es_query)

    def _get_agent_filters(
        agent_params: AgentParameters,
        target_field: Union[str, tuple[str, ...]],
    ) -> None:
        """Get filters relative to agents."""
        if not agent_params:
            return None
        if not isinstance(agent_params, dict):
            agent_params = agent_params.model_dump()

        if not isinstance(target_field, str):
            target_field = ".".join(target_field)

        if agent_params.get("mbox"):
            field = f"{target_field}.mbox.keyword"
            return {"term": {field: agent_params.get("mbox")}}
        elif agent_params.get("mbox_sha1sum"):
            field = f"{target_field}.mbox_sha1sum.keyword"
            return {"term": {field: agent_params.get("mbox_sha1sum")}}
        elif agent_params.get("openid"):
            field = f"{target_field}.openid.keyword"
            return {"term": {field: agent_params.get("openid")}}
        elif agent_params.get("account__name"):
            field_name = f"{target_field}.account.name.keyword"
            field_homepage = f"{target_field}.account.homePage.keyword"
            return {
                "bool": {
                    "filter": [
                        {"term": {field_name: agent_params.get("account__name")}},
                        {
                            "term": {
                                field_homepage: agent_params.get("account__home_page")
                            }
                        },
                    ]
                }
            }
        return None

    @staticmethod
    def _add_agent_filters(
        es_query_filters: list,
        agent_params: AgentParameters,
        target_field: Union[str, tuple[str, ...]],
    ) -> None:
        """Add filters relative to agents to `es_query_filters`."""
        if not agent_params:
            return

        if not isinstance(agent_params, dict):
            agent_params = agent_params.model_dump()

        if not isinstance(target_field, str):
            target_field = ".".join(target_field)

        if agent_params.get("mbox"):
            field = f"{target_field}.mbox.keyword"
            es_query_filters += [{"term": {field: agent_params.get("mbox")}}]
        elif agent_params.get("mbox_sha1sum"):
            field = f"{target_field}.mbox_sha1sum.keyword"
            es_query_filters += [{"term": {field: agent_params.get("mbox_sha1sum")}}]
        elif agent_params.get("openid"):
            field = f"{target_field}.openid.keyword"
            es_query_filters += [{"term": {field: agent_params.get("openid")}}]
        elif agent_params.get("account__name"):
            field_name = f"{target_field}.account.name.keyword"
            field_homepage = f"{target_field}.account.homePage.keyword"
            es_query_filters += [
                {
                    "bool": {
                        "filter": [
                            {"term": {field_name: agent_params.get("account__name")}},
                            {
                                "term": {
                                    field_homepage: agent_params.get(
                                        "account__home_page"
                                    )
                                }
                            },
                        ]
                    }
                }
            ]

    @classmethod
    def _add_related_agent_filters(
        cls, es_query_filters: list, agent_params: AgentParameters
    ) -> None:
        """Add filters relative to agents to `where`, including any 'related agents'."""
        if not agent_params:
            return
        related_filters = []
        for field in RELATED_AGENTS_FIELDS:
            field_filters = cls._get_agent_filters(
                agent_params=agent_params, target_field=field
            )
            if field_filters is not None:
                related_filters.append(field_filters)
        if len(related_filters) > 0:
            es_query_filters += [{"bool": {"should": related_filters}}]
