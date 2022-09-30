"""Elasticsearch database backend for Ralph"""

import json
import logging
from enum import Enum
from typing import Callable, Generator, Optional, TextIO

from elasticsearch import ApiError
from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch import Elasticsearch
from elasticsearch.client import CatClient
from elasticsearch.helpers import BulkIndexError, scan, streaming_bulk

from ralph.conf import settings
from ralph.exceptions import BackendException, BackendParameterException

from .base import (
    BaseDatabase,
    BaseQuery,
    DatabaseStatus,
    StatementParameters,
    StatementQueryResult,
    enforce_query_checks,
)

es_settings = settings.BACKENDS.DATABASE.ES
logger = logging.getLogger(__name__)


class OpType(Enum):
    """Elasticsearch operation types."""

    INDEX = "index"
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"


class ESQuery(BaseQuery):
    """Elasticsearch body query model."""

    query: Optional[dict]


class ESDatabase(BaseDatabase):
    """Elasticsearch database backend."""

    name = "es"
    query_model = ESQuery

    def __init__(
        self,
        hosts: list = es_settings.HOSTS,
        index: str = es_settings.INDEX,
        client_options: dict = es_settings.CLIENT_OPTIONS,
        op_type: str = es_settings.OP_TYPE,
    ):
        """Instantiates the Elasticsearch client.

        Args:
            hosts (list): List of Elasticsearch nodes we should connect to.
            index (str): The Elasticsearch index name.
            client_options (dict): A dictionary of valid options for the
                Elasticsearch class initialization.
            op_type (str): The Elasticsearch operation type for every document sent to
                Elasticsearch (should be one of: index, create, delete, update).
        """
        if client_options is None:
            client_options = {}

        self._hosts = hosts
        self.index = index
        self.client = Elasticsearch(self._hosts, **client_options)
        if op_type not in [op.value for op in OpType]:
            raise BackendParameterException(
                f"{op_type} is not an allowed operation type"
            )
        self.op_type = op_type

    def status(self) -> DatabaseStatus:
        """Checks Elasticsearch cluster (connection) status."""

        # Check ES cluster connection
        try:
            self.client.info()
        except ESConnectionError:
            return DatabaseStatus.AWAY

        # Check cluster status
        if "green" not in CatClient(self.client).health():
            return DatabaseStatus.ERROR

        return DatabaseStatus.OK

    @enforce_query_checks
    def get(self, query: ESQuery = None, chunk_size: int = 500):
        """Gets index documents and yields them.

        The `query` dictionary should only contains kwargs compatible with the
        elasticsearch.helpers.scan function signature (API reference
        documentation:
        https://elasticsearch-py.readthedocs.io/en/latest/helpers.html#scan).
        """

        for document in scan(
            self.client, index=self.index, size=chunk_size, **query.dict()
        ):
            yield document

    def to_documents(
        self, stream: TextIO, get_id: Callable[[dict], str]
    ) -> Generator[dict, None, None]:
        """Converts `stream` lines to ES documents."""

        for line in stream:
            item = json.loads(line) if isinstance(line, str) else line
            action = {
                "_index": self.index,
                "_id": get_id(item),
                "_op_type": self.op_type,
            }
            if self.op_type == "update":
                action.update({"doc": item})
            elif self.op_type in ("create", "index"):
                action.update({"_source": item})
            yield action

    def put(
        self, stream: TextIO, chunk_size: int = 500, ignore_errors: bool = False
    ) -> int:
        """Writes documents from the `stream` to the instance index."""

        logger.debug(
            "Start writing to the %s index (chunk size: %d)", self.index, chunk_size
        )

        documents = 0
        try:
            for success, action in streaming_bulk(
                client=self.client,
                actions=self.to_documents(stream, lambda d: d.get("id", None)),
                chunk_size=chunk_size,
                raise_on_error=(not ignore_errors),
            ):
                documents += success
                logger.debug(
                    "Wrote %d documents [action: %s ok: %d]", documents, action, success
                )
        except BulkIndexError as error:
            raise BackendException(
                *error.args, f"{documents} succeeded writes"
            ) from error
        return documents

    def query_statements(self, params: StatementParameters) -> StatementQueryResult:
        """Returns the results of a statements query using xAPI parameters."""

        es_query_filters = []

        if params.statementId:
            es_query_filters += [{"term": {"_id": params.statementId}}]

        if params.agent:
            es_query_filters += [{"term": {"actor.account.name.keyword": params.agent}}]

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

        if len(es_query_filters) > 0:
            es_query = {"query": {"bool": {"filter": es_query_filters}}}
        else:
            es_query = {"query": {"match_all": {}}}

        # Honor the "ascending" parameter, otherwise show most recent statements first
        es_query.update(
            {"sort": [{"timestamp": {"order": "asc" if params.ascending else "desc"}}]}
        )

        if params.search_after:
            es_query.update({"search_after": params.search_after.split("|")})

        # Disable total hits counting for performance as we're not using it.
        es_query.update({"track_total_hits": False})

        if not params.pit_id:
            pit_response = self._open_point_in_time(
                index=self.index, keep_alive=settings.RUNSERVER_POINT_IN_TIME_KEEP_ALIVE
            )
            params.pit_id = pit_response["id"]

        es_query.update(
            {
                "pit": {
                    "id": params.pit_id,
                    # extend duration of PIT whenever it is used
                    "keep_alive": settings.RUNSERVER_POINT_IN_TIME_KEEP_ALIVE,
                }
            }
        )
        es_response = self._search(body=es_query, size=params.limit)
        es_documents = es_response["hits"]["hits"]
        search_after = None
        if es_documents:
            search_after = "|".join([str(part) for part in es_documents[-1]["sort"]])

        return StatementQueryResult(
            statements=[document["_source"] for document in es_documents],
            pit_id=es_response["pit_id"],
            search_after=search_after,
        )

    def query_statements_by_ids(self, ids: list[str]) -> list:
        """Returns the list of matching statement IDs from the database."""

        body = {"query": {"terms": {"_id": ids}}}
        return self._search(index=self.index, body=body)["hits"]["hits"]

    def _search(self, **kwargs):
        """Wraps the ElasticSearch.search method to raise a BackendException in case
        of any failure.
        """

        try:
            return self.client.search(**kwargs)
        except ApiError as error:
            msg = "Failed to execute ElasticSearch query"
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error

    def _open_point_in_time(self, **kwargs):
        """Wraps the ElasticSearch.open_point_in_time method to raise a BackendException
        in case of any failure.
        """

        try:
            return self.client.open_point_in_time(**kwargs)
        except (ApiError, ValueError) as error:
            msg = "Failed to open ElasticSearch point in time"
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error
