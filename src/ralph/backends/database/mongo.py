"""MongoDB database backend for Ralph"""

import hashlib
import json
import logging
import struct
from typing import Generator, Optional, TextIO, Union

from bson.objectid import ObjectId
from dateutil.parser import isoparse
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import BulkWriteError, PyMongoError

from ralph.conf import settings
from ralph.exceptions import BackendException, BadFormatException

from .base import (
    BaseDatabase,
    BaseQuery,
    StatementParameters,
    StatementQueryResult,
    enforce_query_checks,
)

mongo_settings = settings.BACKENDS.DATABASE.MONGO
logger = logging.getLogger(__name__)


class MongoQuery(BaseQuery):
    """Mongo query model."""

    filter: Optional[dict]
    projection: Optional[dict]


class MongoDatabase(BaseDatabase):
    """Mongo database backend."""

    name = "mongo"
    query_model = MongoQuery

    def __init__(
        self,
        connection_uri: str = mongo_settings.CONNECTION_URI,
        database: str = mongo_settings.DATABASE,
        collection: str = mongo_settings.COLLECTION,
        client_options: dict = mongo_settings.CLIENT_OPTIONS,
    ):
        """Instantiates the Mongo client.

        Args:
            connection_uri (str): MongoDB connection URI.
            database (str): MongoDB database to connect to.
            collection (str): MongoDB database collection to get objects from.
            client_options (dict): A dictionary of valid options for the MongoClient
                class initialization.
        """
        if client_options is None:
            client_options = {}

        self.client = MongoClient(connection_uri, **client_options)
        self.database = getattr(self.client, database)
        self.collection = getattr(self.database, collection)

    @enforce_query_checks
    def get(self, query: MongoQuery = None, chunk_size: int = 500):
        """Gets collection documents and yields them.

        The `query` dictionary should only contain kwargs compatible with the
        pymongo.collection.Collection.find method signature (API reference
        documentation: https://pymongo.readthedocs.io/en/stable/api/pymongo/).
        """

        for document in self.collection.find(batch_size=chunk_size, **query.dict()):
            # Make the document json-serializable
            document.update({"_id": str(document.get("_id"))})
            yield document

    @staticmethod
    def to_documents(
        stream: Union[TextIO, list], ignore_errors: bool = False
    ) -> Generator[dict, None, None]:
        """Converts `stream` lines (one statement per line) to Mongo documents.

        We expect statements to have at least an `id` and a `timestamp` field that will
        be used to compute a unique MongoDB Object ID. This ensures that we will not
        duplicate statements in our database and allows us to support pagination.
        """

        for line in stream:
            statement = json.loads(line) if isinstance(line, str) else line
            if "id" not in statement:
                msg = f"statement {statement} has no 'id' field"
                if ignore_errors:
                    logger.warning(msg)
                    continue
                raise BadFormatException(msg)
            if "timestamp" not in statement:
                msg = f"statement {statement} has no 'timestamp' field"
                if ignore_errors:
                    logger.warning(msg)
                    continue
                raise BadFormatException(msg)
            try:
                timestamp = int(isoparse(statement["timestamp"]).timestamp())
            except ValueError as err:
                msg = f"statement {statement} has an invalid 'timestamp' field"
                if ignore_errors:
                    logger.warning(msg)
                    continue
                raise BadFormatException(msg) from err
            document = {
                "_id": ObjectId(
                    # This might become a problem in February 2106.
                    # Meanwhile, we use the timestamp in the _id field for pagination.
                    struct.pack(">I", timestamp)
                    + bytes.fromhex(
                        hashlib.sha256(bytes(statement["id"], "utf-8")).hexdigest()[:16]
                    )
                ),
                "_source": statement,
            }

            yield document

    def bulk_import(self, batch: list, ignore_errors: bool = False):
        """Inserts a batch of documents into the selected database collection."""

        try:
            new_documents = self.collection.insert_many(batch)
        except BulkWriteError as error:
            if not ignore_errors:
                raise BackendException(
                    *error.args, f"{error.details['nInserted']} succeeded writes"
                ) from error
            logger.warning(
                "Bulk importation failed for current documents chunk but you choose "
                "to ignore it.",
            )
            return error.details["nInserted"]

        inserted_count = len(new_documents.inserted_ids)
        logger.debug("Inserted %d documents chunk with success", inserted_count)

        return inserted_count

    def put(
        self,
        stream: Union[TextIO, list],
        chunk_size: int = 500,
        ignore_errors: bool = False,
    ) -> int:
        """Writes documents from the `stream` to the instance collection."""

        logger.debug(
            "Start writing to the %s collection of the %s database (chunk size: %d)",
            self.collection,
            self.database,
            chunk_size,
        )

        success = 0
        batch = []
        for document in self.to_documents(stream, ignore_errors=ignore_errors):

            batch.append(document)
            if len(batch) < chunk_size:
                continue

            success += self.bulk_import(batch, ignore_errors=ignore_errors)
            batch = []

        # Edge case: if the total number of documents is lower than the chunk size
        if len(batch) > 0:
            success += self.bulk_import(batch, ignore_errors=ignore_errors)

        logger.debug("Inserted a total of %d documents with success", success)

        return success

    def query_statements(self, params: StatementParameters) -> StatementQueryResult:
        """Returns the results of a statements query using xAPI parameters."""

        mongo_query_filters = {}

        if params.statementId:
            mongo_query_filters.update({"_source.id": params.statementId})

        if params.agent:
            mongo_query_filters.update({"_source.actor.account.name": params.agent})

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
            mongo_query_filters.update({"_source.timestamp": {"$lte": params.until}})

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

        mongo_response = self._find(
            filter=mongo_query_filters, limit=params.limit, sort=mongo_query_sort
        )
        search_after = None
        if mongo_response:
            search_after = mongo_response[-1]["_id"]

        return StatementQueryResult(
            statements=[document["_source"] for document in mongo_response],
            pit_id=None,
            search_after=search_after,
        )

    def query_statements_by_ids(self, ids: list[str]) -> list:
        """Returns the list of matching statement IDs from the database."""

        return self._find(filter={"_source.id": {"$in": ids}})

    def _find(self, **kwargs):
        """Wraps the MongoClient.collection.find method to raise a BackendException in
        case of any failure.
        """

        try:
            return list(self.collection.find(**kwargs))
        except (PyMongoError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute MongoDB query"
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error
