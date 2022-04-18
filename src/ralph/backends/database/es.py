"""Elasticsearch storage backend for Ralph"""

import json
import logging
from enum import Enum
from typing import Callable, Generator, TextIO

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, streaming_bulk

from ralph.defaults import (
    ES_HOSTS,
    ES_INDEX,
    ES_MAX_SEARCH_HITS_COUNT,
    ES_POINT_IN_TIME_KEEP_ALIVE,
)
from ralph.exceptions import BackendParameterException

from .base import BaseDatabase

logger = logging.getLogger(__name__)


class OpType(Enum):
    """Elasticsearch operation types."""

    INDEX = "index"
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"


DEFAULT_OP_TYPE = OpType.INDEX.value


class ESDatabase(BaseDatabase):
    """Elasticsearch database backend."""

    name = "es"

    def __init__(
        self,
        hosts: list = ES_HOSTS,
        index: str = ES_INDEX,
        client_options: dict = None,
        op_type: str = DEFAULT_OP_TYPE,
    ):
        """Instantiates the Elasticsearch client.

        Args:
            hosts (list): List of Elasticsearch nodes we should connect to.
            index (str): The Elasticsearch index name.
            es_client_options (dict): A dictionary of valid options for the
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

    def get(self, chunk_size: int = 500):
        """Gets index documents and yields them."""

        for document in scan(self.client, index=self.index, size=chunk_size):
            yield document

    def query(self, body: dict, size=ES_MAX_SEARCH_HITS_COUNT, pit_id=None, **kwargs):
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
                index=self.index, keep_alive=ES_POINT_IN_TIME_KEEP_ALIVE
            )
            pit_id = pit_response["id"]

        body.update(
            {
                "pit": {
                    "id": pit_id,
                    # extend duration of PIT whenever it is used
                    "keep_alive": ES_POINT_IN_TIME_KEEP_ALIVE,
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

    def put(self, stream: TextIO, chunk_size: int = 500, ignore_errors: bool = False):
        """Writes documents from the `stream` to the instance index."""

        logger.debug(
            "Start writing to the %s index (chunk size: %d)", self.index, chunk_size
        )

        documents = 0
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
