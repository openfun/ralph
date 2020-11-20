"""Elasticsearch storage backend for Ralph"""

import json
import logging
import sys

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, streaming_bulk

from .base import BaseDatabase

logger = logging.getLogger(__name__)


class ESDatabase(BaseDatabase):
    """Elasticsearch database backend"""

    name = "es"

    def __init__(self, hosts, index, verify_certs=True):
        """Instantiate the Elasticsearch client.

        hosts is supposed to be a list

        """

        self._hosts = hosts
        self.index = index
        self.client = Elasticsearch(self._hosts, verify_certs=verify_certs)

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
            yield {
                "_index": self.index,
                "_id": get_id(item),
                "_source": item,
            }

    def put(self, chunk_size=500):
        """Write documents streamed from the standard input to the instance index"""

        logger.debug(
            "Start writing to the %s index (chunk size: %d)", self.index, chunk_size
        )

        documents = 0
        for success, action in streaming_bulk(
            client=self.client,
            actions=self.to_documents(sys.stdin, lambda d: d.get("id", None)),
            chunk_size=chunk_size,
        ):
            documents += success
            logger.debug(
                "Wrote %d documents [action: %s ok: %d]", documents, action, success
            )
