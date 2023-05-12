"""MongoDB data backend for Ralph."""

import hashlib
import json
import logging
import struct
from io import IOBase
from itertools import chain
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Union,
)
from uuid import uuid4

from bson.objectid import ObjectId
from dateutil.parser import isoparse
from pydantic import Json
from pymongo import ASCENDING, DESCENDING, MongoClient, ReplaceOne
from pymongo.errors import BulkWriteError, ConnectionFailure, PyMongoError

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
    enforce_query_checks,
)
from ralph.backends.lrs.base import (
    BaseLRSBackend,
    StatementParameters,
    StatementQueryResult,
)
from ralph.conf import BaseSettingsConfig, MongoClientOptions
from ralph.exceptions import (
    BackendException,
    BackendParameterException,
    BadFormatException,
)

logger = logging.getLogger(__name__)


class MongoDataBackendSettings(BaseDataBackendSettings):
    """Represents the Mongo data backend default configuration.

    Attributes:
        CONNECTION_URI (str): The MongoDB connection URI.
        DATABASE (str): The MongoDB database to connect to.
        DEFAULT_COLLECTION (str): The MongoDB database collection to get objects from.
        CLIENT_OPTIONS (MongoClientOptions): A dictionary of valid options
        DEFAULT_QUERY_STRING (str): The default query string to use.
        DEFAULT_CHUNK_SIZE (int): The default chunk size to use when none is provided.
        LOCALE_ENCODING (str): The locale encoding to use when none is provided.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__MONGO__"

    CONNECTION_URI: str = None
    DATABASE: str = None
    DEFAULT_COLLECTION: str = None
    CLIENT_OPTIONS: MongoClientOptions = MongoClientOptions()
    DEFAULT_QUERY_STRING: str = "*"
    DEFAULT_CHUNK_SIZE: int = 500
    LOCALE_ENCODING: str = "utf8"


class MongoQuery(BaseQuery):
    """Mongo query model."""

    # pylint: disable=unsubscriptable-object
    query_string: Optional[
        Json[
            Dict[
                Literal["filter", "projection"],
                dict,
            ]
        ]
    ]
    filter: Optional[dict]
    projection: Optional[dict]


class MongoDataBackend(BaseDataBackend):
    """Mongo database backend."""

    name = "mongo"
    query_model = MongoQuery
    default_operation_type = BaseOperationType.CREATE
    settings_class = MongoDataBackendSettings

    def __init__(self, settings: settings_class = None):
        """Instantiates the Mongo client.

        Args:
            settings (MongoDataBackendSettings): The Mongo data backend settings.
            CONNECTION_URI (str): The MongoDB connection URI.
            DATABASE (str): The MongoDB database to connect to.
            DEFAULT_COLLECTION (str): The MongoDB database collection.
            CLIENT_OPTIONS (MongoClientOptions): A dictionary of valid options
            DEFAULT_QUERY_STRING (str): The default query string to use.
            DEFAULT_CHUNK_SIZE (int): The default chunk size to use.
            LOCALE_ENCODING (str): The locale encoding to use when none is provided.
        """
        self.client = MongoClient(
            settings.CONNECTION_URI, **settings.CLIENT_OPTIONS.dict()
        )
        self.database = getattr(self.client, settings.DATABASE)
        self.collection = getattr(self.database, settings.DEFAULT_COLLECTION)
        self.default_chunk_size = settings.DEFAULT_CHUNK_SIZE
        self.locale_encoding = settings.LOCALE_ENCODING

    def status(self) -> DataBackendStatus:
        """Checks MongoDB cluster connection status."""
        # Check Mongo cluster connection
        try:
            self.client.admin.command("ping")
        except ConnectionFailure:
            return DataBackendStatus.AWAY

        # Check cluster status
        if self.client.admin.command("serverStatus").get("ok", 0.0) < 1.0:
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: str = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """Lists collections for a given database.

        Args:
            target (str): The database to list collections from.
            details (bool): Get detailed archive information instead of just ids.
            new (bool): Given the history, list only not already fetched collections.
        """
        database = self.database if not target else getattr(self.client, target)
        for col in database.list_collections():
            if details:
                yield col
            else:
                yield str(col.get("name"))

    @enforce_query_checks
    def read(
        self,
        *,
        query: Union[str, MongoQuery] = None,
        target: str = None,
        chunk_size: Union[None, int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Gets collection documents and yields them.

        Args:
            query (Union[str, MongoQuery]): The query to use when fetching documents.
            target (str): The collection to get documents from.
            chunk_size (Union[None, int]): The chunk size to use when fetching docs.
            raw_output (bool): Whether to return raw bytes or deserialized documents.
            ignore_errors (bool): Whether to ignore errors when reading documents.
        """
        reader = self._read_raw if raw_output else self._read_dict
        if not chunk_size:
            chunk_size = self.default_chunk_size
        find_kwargs = {}
        if query.query_string:
            find_kwargs = query.query_string
        else:
            find_kwargs = {"filter": query.filter, "projection": query.projection}

        # deserialize query_string if exists
        for document in self._find(target=target, batch_size=chunk_size, **find_kwargs):
            document.update({"_id": str(document.get("_id"))})
            yield reader(document)

    @staticmethod
    def to_documents(
        data: Iterable[dict],
        ignore_errors: bool = False,
        operation_type: Union[None, BaseOperationType] = default_operation_type,
    ) -> Generator[dict, None, None]:
        """Converts `stream` lines (one statement per line) to Mongo documents.

        We expect statements to have at least an `id` and a `timestamp` field that will
        be used to compute a unique MongoDB Object ID. This ensures that we will not
        duplicate statements in our database and allows us to support pagination.
        """
        for statement in data:
            if "id" not in statement and operation_type == BaseOperationType.CREATE:
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
                        hashlib.sha256(
                            bytes(statement.get("id", str(uuid4())), "utf-8")
                        ).hexdigest()[:16]
                    )
                ),
                "_source": statement,
            }

            yield document

    def bulk_import(self, batch: list, ignore_errors: bool = False, collection=None):
        """Inserts a batch of documents into the selected database collection."""
        try:
            collection = self.get_collection(collection)
            new_documents = collection.insert_many(batch)
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

    def bulk_delete(self, batch: list, collection=None):
        """Deletes a batch of documents from the selected database collection."""
        collection = self.get_collection(collection)
        new_documents = collection.delete_many({"_source.id": {"$in": batch}})
        deleted_count = new_documents.deleted_count
        logger.debug("Deleted %d documents chunk with success", deleted_count)

        return deleted_count

    def bulk_update(self, batch: list, collection=None):
        """Update a batch of documents into the selected database collection."""
        collection = self.get_collection(collection)
        new_documents = collection.bulk_write(batch)
        modified_count = new_documents.modified_count
        logger.debug("Updated %d documents chunk with success", modified_count)
        return modified_count

    def get_collection(self, collection=None):
        """Returns the collection to use for the current operation."""
        if collection is None:
            collection = self.collection
        elif isinstance(collection, str):
            collection = getattr(self.database, collection)
        return collection

    def write(  # pylint: disable=too-many-arguments disable=too-many-branches
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[None, str] = None,
        chunk_size: Union[None, int] = None,
        ignore_errors: bool = False,
        operation_type: Union[None, BaseOperationType] = None,
    ) -> int:
        """Writes documents from the `stream` to the instance collection.

        Args:
            data: The data to write to the database.
            target: The target collection to write to.
            chunk_size: The number of documents to write at once.
            ignore_errors: Whether to ignore errors or not.
            operation_type: The operation type to use for the write operation.
        """
        if not operation_type:
            operation_type = self.default_operation_type

        if not chunk_size:
            chunk_size = self.default_chunk_size

        collection = self.get_collection(target)
        logger.debug(
            "Start writing to the %s collection of the %s database (chunk size: %d)",
            collection,
            self.database,
            chunk_size,
        )

        data = iter(data)
        try:
            first_record = next(data)
            data = chain([first_record], data)
            if isinstance(first_record, bytes):
                data = self._parse_bytes_to_dict(data, ignore_errors)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return 0

        success = 0
        batch = []
        if operation_type == BaseOperationType.UPDATE:
            for document in data:
                document_id = document.get("id")
                batch.append(
                    ReplaceOne(
                        {"_source.id": {"$eq": document_id}},
                        {"_source": document},
                    )
                )
                if len(batch) >= chunk_size:
                    success += self.bulk_update(batch, collection=collection)
                    batch = []

            if len(batch) > 0:
                success += self.bulk_update(batch, collection=collection)

            logger.debug("Updated %d documents chunk with success", success)
        elif operation_type == BaseOperationType.DELETE:
            for document in data:
                document_id = document.get("id")
                batch.append(document_id)
                if len(batch) >= chunk_size:
                    success += self.bulk_delete(batch, collection=collection)
                    batch = []

            if len(batch) > 0:
                success += self.bulk_delete(batch, collection=collection)

            logger.debug("Deleted %d documents chunk with success", success)
        elif operation_type in [BaseOperationType.INDEX, BaseOperationType.CREATE]:
            for document in self.to_documents(
                data, ignore_errors=ignore_errors, operation_type=operation_type
            ):
                batch.append(document)
                if len(batch) >= chunk_size:
                    success += self.bulk_import(
                        batch, ignore_errors=ignore_errors, collection=collection
                    )
                    batch = []

            # Edge case: if the total number of documents is lower than the chunk size
            if len(batch) > 0:
                success += self.bulk_import(
                    batch, ignore_errors=ignore_errors, collection=collection
                )

            logger.debug("Inserted %d documents with success", success)
        else:
            msg = "%s operation_type is not allowed."
            logger.error(msg, operation_type.name)
            raise BackendParameterException(msg % operation_type.name)
        return success

    def _find(self, target: Union[None, str] = None, **kwargs):
        """Wraps the MongoClient.collection.find method.

        Raises:
            BackendException: raised for any failure.
        """
        try:
            collection = self.get_collection(target)
            return list(collection.find(**kwargs))
        except (PyMongoError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute MongoDB query"
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error

    @staticmethod
    def _parse_bytes_to_dict(
        raw_documents: Iterable[bytes], ignore_errors: bool
    ) -> Iterator[dict]:
        """Reads the `raw_documents` Iterable and yields dictionaries."""
        for raw_document in raw_documents:
            try:
                decoded_item = raw_document.decode("utf-8")
                json_data = json.loads(decoded_item)
                yield json_data
            except (TypeError, json.JSONDecodeError) as err:
                logger.error("Raised error: %s, for document %s", err, raw_document)
                if ignore_errors:
                    continue
                raise err

    def _read_raw(self, document: Dict[str, Any]) -> bytes:
        """Reads the `documents` Iterable and yields bytes."""
        return json.dumps(document).encode(self.locale_encoding)

    @staticmethod
    def _read_dict(document: Dict[str, Any]) -> dict:
        """Reads the `documents` Iterable and yields dictionaries."""
        return document


class MongoLRSBackend(BaseLRSBackend, MongoDataBackend):
    """MongoDB LRS backend implementation."""

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

    def query_statements_by_ids(self, ids: List[str]) -> List:
        """Returns the list of matching statement IDs from the database."""
        return self._find(filter={"_source.id": {"$in": ids}})
