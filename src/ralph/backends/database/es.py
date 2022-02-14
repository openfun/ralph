"""Elasticsearch storage backend for Ralph"""

import json
import logging
import sys
from enum import Enum

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import scan, streaming_bulk

from ralph.exceptions import BackendParameterException

from .base import BaseDatabase

logger = logging.getLogger(__name__)


VOID_STATEMENT_ID = "http://adlnet.gov/expapi/verbs/voided"


STATEMENTS_MAPPING = {
    "properties": {
        "activity": {"type": "keyword"},
        "is_voided": {"type": "boolean"},
        "registration": {"type": "keyword"},
        "related_activities": {"type": "keyword"},
        "timestamp": {"type": "date"},
        "verb": {"type": "keyword"},
    }
}


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
        self.indices_client = IndicesClient(self.client)

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

    @staticmethod
    def get_related_activities_for_statement(statement):
        """
        Create the related activities list for a given statement to index. This powers
        the "activity" filter when expanded by the "related_activities" parameter
        """
        # The relevant statements to consider include the statement itself,
        # and a SubStatement it may contain
        relevant_statements = [statement]
        if statement.get("object", {}).get("objectType", None) == "SubStatement":
            relevant_statements += statement.get("object")

        related_activities = []
        for statement in relevant_statements:
            # The object of the statement is part of the related activities
            related_activities += statement.get("object", {})
            # Loop through the context activities to add them to the related activities
            context_activities = item.get("contextActivities", {})
            related_activities += (
                context_activities.get("parent", [])
                + context_activities.get("category", [])
                + context_activities.get("other", [])
            )

        # Only consider actual activities defined as objects with object type "Activity"
        related_activities = filter(
            lambda activity: activity.get("objectType", None) == "Activity",
            related_activities,
        )

        return [activity["id"] for activity in related_activities]

    @classmethod
    def get_es_document_for_statement(
        self, statement, index="statements", op_type="index"
    ):
        """
        Build out the statement as necessary for indexation into ElasticSearch.
        """

        action = {
            "_index": self.index,
            "_id": get_id(statement),
            "_op_type": self.op_type,
            "is_voided": False,
            "registration": statement.get("context", {}).get("registration", None),
            "related_activities": self.get_related_activities_for_statement(statement),
            "timestamp": statement.get("timestamp", None),
            "verb": statement.get("verb", {}).get("id", None),
        }

        # The activity filter only relates to objects with an "Activity" type
        statement_object = statement.get("object", {})
        action.update(
            {
                "activity": statement_object["id"]
                if statement.get("objectType", None) == "Activity"
                else None
            }
        )

        if self.op_type == "update":
            action.update(
                {
                    "doc": statement,
                }
            )
        elif self.op_type in ("create", "index"):
            action.update(
                {
                    "_source": statement,
                }
            )

        return action

    def to_documents(self, stream, get_id):
        """Convert stream lines to ES documents"""

        for line in stream:
            item = json.loads(line)

            yield self.get_es_document_for_statement(
                item, index=self.index, op_type=self.op_type
            )

            # Special case for voiding statements: in addition to indexing the voiding
            # statement itself, issue an update for the voided statement
            if (
                item.get("verb", {}).get("id", None) == VOID_STATEMENT_ID
                and item.get("object", {}).get("objectType", "StatementRef")
                and item["object"].get("id", None)
            ):
                yield {
                    "_id": item["object"]["id"],
                    "_index": self.index,
                    "_op_type": "update",
                    "is_voided": True,
                }

    def put(self, chunk_size=500, ignore_errors=False):
        """Write documents streamed from the standard input to the instance index"""

        logger.debug(
            "Start writing to the %s index (chunk size: %d)", self.index, chunk_size
        )

        self.indices_client.put_mapping(STATEMENTS_MAPPING, index=self.index)

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
