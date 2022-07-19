"""MongoDB database backend for Ralph"""

import hashlib
import json
import logging
from typing import Generator, Optional, TextIO, Union

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from ralph.defaults import get_settings
from ralph.exceptions import BadFormatException

from .base import BaseDatabase, BaseQuery, enforce_query_checks

logger = logging.getLogger(__name__)
settings = get_settings()


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
        connection_uri: str = settings.MONGO_CONNECTION_URI,
        database: str = settings.MONGO_DATABASE,
        collection: str = settings.MONGO_COLLECTION,
        client_options: dict = None,
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

        We expect statements to have at least an `id` field that will be used
        to compute a unique MongoDB Object ID. This ensures that we will not
        duplicate statements in our database.
        """

        for line in stream:
            statement = json.loads(line) if isinstance(line, str) else line
            if "id" not in statement:
                msg = f"statement {statement} has no 'id' field"
                if ignore_errors:
                    logger.warning(msg)
                    continue
                raise BadFormatException(msg)
            document = {
                "_id": ObjectId(
                    hashlib.sha256(bytes(statement["id"], "utf-8")).hexdigest()[:24]
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
                raise error
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
