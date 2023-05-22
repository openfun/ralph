"""Elasticsearch LRS backend for Ralph."""

import logging
from typing import Iterator, List

from ralph.backends.data.es import ESDataBackend, ESQuery, ESQueryPit
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    StatementParameters,
    StatementQueryResult,
)
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class ESLRSBackend(BaseLRSBackend, ESDataBackend):
    """Elasticsearch LRS backend implementation."""

    settings_class = ESDataBackend.settings_class

    def query_statements(self, params: StatementParameters) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        es_query_filters = []

        if params.statementId:
            es_query_filters += [{"term": {"_id": params.statementId}}]

        self._add_agent_filters(es_query_filters, params.agent, "actor")
        self._add_agent_filters(es_query_filters, params.authority, "authority")

        if params.verb:
            es_query_filters += [{"term": {"verb.id.keyword": params.verb}}]

        if params.activity:
            es_query_filters += [
                {"term": {"object.objectType.keyword": "Activity"}},
                {"term": {"object.id.keyword": params.activity}},
            ]

        if params.since:
            es_query_filters += [{"range": {"timestamp": {"gt": params.since}}}]

        if params.until:
            es_query_filters += [{"range": {"timestamp": {"lte": params.until}}}]

        es_query = {
            "pit": ESQueryPit.construct(id=params.pit_id),
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
        query = ESQuery.construct(**es_query)
        try:
            es_documents = self.read(query=query, chunk_size=params.limit)
            statements = [document["_source"] for document in es_documents]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

        return StatementQueryResult(
            statements=statements,
            pit_id=query.pit.id,
            search_after="|".join(query.search_after) if query.search_after else "",
        )

    def query_statements_by_ids(self, ids: List[str]) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        try:
            es_response = self.read(query={"query": {"terms": {"_id": ids}}})
            yield from (document["_source"] for document in es_response)
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

    @staticmethod
    def _add_agent_filters(
        es_query_filters: list, agent_params: AgentParameters, target_field: str
    ):
        """Add filters relative to agents to `es_query_filters`."""
        if not agent_params:
            return
        if agent_params.mbox:
            field = f"{target_field}.mbox.keyword"
            es_query_filters += [{"term": {field: agent_params.mbox}}]
        elif agent_params.mbox_sha1sum:
            field = f"{target_field}.mbox_sha1sum.keyword"
            es_query_filters += [{"term": {field: agent_params.mbox_sha1sum}}]
        elif agent_params.openid:
            field = f"{target_field}.openid.keyword"
            es_query_filters += [{"term": {field: agent_params.openid}}]
        elif agent_params.account__name:
            field = f"{target_field}.account.name.keyword"
            es_query_filters += [{"term": {field: agent_params.account__name}}]
            field = f"{target_field}.account.homePage.keyword"
            es_query_filters += [{"term": {field: agent_params.account__home_page}}]