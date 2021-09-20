"""Elasticsearch storage backend for Ralph"""

import json
import logging
import sys
from enum import Enum

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, streaming_bulk

from ralph.exceptions import BackendParameterException

from .base import BaseDatabase

logger = logging.getLogger(__name__)


class OpType(Enum):
    """Elasticsearch operation types"""

    INDEX = "index"
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"


DEFAULT_OP_TYPE = OpType.INDEX.value


class ESDatabase(BaseDatabase):
    """Elasticsearch database backend"""

    name = "es"

    def __init__(
        self,
        hosts: list,
        index: str,
        client_options: dict = None,
        op_type: str = DEFAULT_OP_TYPE,
    ):
        """Instantiate the Elasticsearch client.

        hosts: supposed to be a list
        index: the index name
        es_client_options: a dict of valid options for the Elasticsearch class
                           initialization
        op_type: elasticsearch operation type for every document sent to ES
                (should be one of: index, create, delete, update)

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

    def get(self, chunk_size=500):
        """Get index documents and stream them"""

        for document in scan(self.client, index=self.index, size=chunk_size):
            sys.stdout.buffer.write(
                bytes(json.dumps(document.get("_source")) + "\n", encoding="utf-8")
            )

    def to_documents(self, stream, get_id):
        """Convert stream lines to ES documents"""

        for line in stream:
            item = json.loads(line)
            action = {
                "_index": self.index,
                "_id": get_id(item),
                "_op_type": self.op_type,
            }
            if self.op_type == "update":
                action.update(
                    {
                        "doc": item,
                    }
                )
            elif self.op_type in ("create", "index"):
                action.update(
                    {
                        "_source": item,
                    }
                )
            yield action

    def put(self, chunk_size=500, ignore_errors=False):
        """Write documents streamed from the standard input to the instance index"""

        logger.debug(
            "Start writing to the %s index (chunk size: %d)", self.index, chunk_size
        )

        documents = 0
        for success, action in streaming_bulk(
            client=self.client,
            actions=self.to_documents(sys.stdin, lambda d: d.get("id", None)),
            chunk_size=chunk_size,
            raise_on_error=(not ignore_errors),
        ):
            documents += success
            logger.debug(
                "Wrote %d documents [action: %s ok: %d]", documents, action, success
            )
