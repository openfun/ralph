"""Elasticsearch database backend for Ralph"""

import json
import logging
from enum import Enum
from typing import Callable, Generator, Optional, TextIO

from elasticsearch import Elasticsearch
from elasticsearch.helpers import BulkIndexError, scan, streaming_bulk

from ralph.defaults import get_settings
from ralph.exceptions import BackendParameterException

from .base import BaseDatabase, BaseQuery, enforce_query_checks

logger = logging.getLogger(__name__)
settings = get_settings()


class OpType(Enum):
    """Elasticsearch operation types."""

    INDEX = "index"
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"


DEFAULT_OP_TYPE = OpType.INDEX.value


class ESQuery(BaseQuery):
    """Elasticsearch body query model."""

    query: Optional[dict]


class ESDatabase(BaseDatabase):
    """Elasticsearch database backend."""

    name = "es"
    query_model = ESQuery

    def __init__(
        self,
        hosts: list = settings.ES_HOSTS,
        index: str = settings.ES_INDEX,
        client_options: dict = None,
        op_type: str = DEFAULT_OP_TYPE,
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

    @enforce_query_checks
    def get(self, query: ESQuery = None, chunk_size: int = 500):
        """Gets index documents and yields them.

        The `query` dictionnary should only contains kwargs compatible with the
        elasticsearch.helpers.scan function signature (API reference
        documentation:
        https://elasticsearch-py.readthedocs.io/en/latest/helpers.html#scan).
        """

        for document in scan(
            self.client, index=self.index, size=chunk_size, **query.dict()
        ):
            yield document

    def query(
        self,
        body: dict,
        size=settings.RUNSERVER_MAX_SEARCH_HITS_COUNT,
        pit_id=None,
        **kwargs,
    ):
        """Returns the Elasticsearch query results.

        Args:
            body (dict): The Elasticsearch query definition (Query DSL).
            size (int): The (maximal) number of results to return.
            pit_id (string): Limits the search to a point in time.
            **kwargs: Additional arguments for the `Elasticsearch.search` method.
        """
        # pylint: disable=unexpected-keyword-arg

        # Create a point-in-time or use the existing one to ensure consistency of search
        # results over multiple pages.
        if not pit_id:
            pit_response = self.client.open_point_in_time(
                index=self.index, keep_alive=settings.RUNSERVER_POINT_IN_TIME_KEEP_ALIVE
            )
            pit_id = pit_response["id"]

        body.update(
            {
                "pit": {
                    "id": pit_id,
                    # extend duration of PIT whenever it is used
                    "keep_alive": settings.RUNSERVER_POINT_IN_TIME_KEEP_ALIVE,
                }
            }
        )

        return self.client.search(body=body, size=size, **kwargs)

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
            error.args = error.args + (f"{documents} succeeded",)
            raise error
        return documents
