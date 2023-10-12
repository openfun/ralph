"""MongoDB data backend for Ralph."""

from __future__ import annotations

import hashlib
import logging
import struct
from io import IOBase
from itertools import chain
from typing import Generator, Iterable, Iterator, List, Tuple, Union
from uuid import uuid4

from bson.errors import BSONError
from bson.objectid import ObjectId
from dateutil.parser import isoparse
from pydantic import Json, MongoDsn, constr
from pymongo import MongoClient, ReplaceOne
from pymongo.collection import Collection
from pymongo.errors import (
    BulkWriteError,
    ConnectionFailure,
    InvalidName,
    InvalidOperation,
    PyMongoError,
)

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
    enforce_query_checks,
)
from ralph.conf import BaseSettingsConfig, ClientOptions
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import parse_bytes_to_dict, read_raw

logger = logging.getLogger(__name__)


class MongoClientOptions(ClientOptions):
    """MongoDB additional client options."""

    document_class: str = None
    tz_aware: bool = None


class MongoDataBackendSettings(BaseDataBackendSettings):
    """MongoDB data backend default configuration.

    Attributes:
        CONNECTION_URI (str): The MongoDB connection URI.
        DEFAULT_DATABASE (str): The MongoDB database to connect to.
        DEFAULT_COLLECTION (str): The MongoDB database collection to get objects from.
        CLIENT_OPTIONS (MongoClientOptions): A dictionary of MongoDB client options.
        DEFAULT_CHUNK_SIZE (int): The default chunk size to use when none is provided.
        LOCALE_ENCODING (str): The locale encoding to use when none is provided.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__MONGO__"

    CONNECTION_URI: MongoDsn = MongoDsn("mongodb://localhost:27017/", scheme="mongodb")
    DEFAULT_DATABASE: constr(regex=r"^[^\s.$/\\\"\x00]+$") = "statements"  # noqa : F722
    DEFAULT_COLLECTION: constr(
        regex=r"^(?!.*\.\.)[^.$\x00]+(?:\.[^.$\x00]+)*$"  # noqa : F722
    ) = "marsha"
    CLIENT_OPTIONS: MongoClientOptions = MongoClientOptions()
    DEFAULT_CHUNK_SIZE: int = 500
    LOCALE_ENCODING: str = "utf8"


class BaseMongoQuery(BaseQuery):
    """Base MongoDB query model."""

    filter: Union[dict, None]
    limit: Union[int, None]
    projection: Union[dict, None]
    sort: Union[List[Tuple], None]


class MongoQuery(BaseMongoQuery):
    """MongoDB query model."""

    # pylint: disable=unsubscriptable-object
    query_string: Union[Json[BaseMongoQuery], None]


class MongoDataBackend(BaseDataBackend):
    """MongoDB data backend."""

    name = "mongo"
    query_model = MongoQuery
    settings_class = MongoDataBackendSettings

    def __init__(self, settings: Union[settings_class, None] = None):
        """Instantiate the MongoDB client.

        Args:
            settings (MongoDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings = settings if settings else self.settings_class()
        self.client = MongoClient(
            self.settings.CONNECTION_URI, **self.settings.CLIENT_OPTIONS.dict()
        )
        self.database = self.client[self.settings.DEFAULT_DATABASE]
        self.collection = self.database[self.settings.DEFAULT_COLLECTION]

    def status(self) -> DataBackendStatus:
        """Check the MongoDB connection status.

        Returns:
            DataBackendStatus: The status of the data backend.
        """
        # Check MongoDB connection.
        try:
            self.client.admin.command("ping")
        except (ConnectionFailure, InvalidOperation) as error:
            logger.error("Failed to connect to MongoDB: %s", error)
            return DataBackendStatus.AWAY

        # Check MongoDB server status.
        try:
            if self.client.admin.command("serverStatus").get("ok") != 1.0:
                logger.error("MongoDB `serverStatus` command did not return 1.0")
                return DataBackendStatus.ERROR
        except PyMongoError as error:
            logger.error("Failed to get MongoDB server status: %s", error)
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List collections in the `target` database.

        Args:
            target (str or None): The MongoDB database name to list collections from.
                If target is `None`, the `DEFAULT_DATABASE` is used instead.
            details (bool): Get detailed collection information instead of just IDs.
            new (bool): Ignored.

        Raises:
            BackendException: If a failure during the list operation occurs.
            BackendParameterException: If the `target` is not a valid database name.
        """
        if new:
            logger.warning("The `new` argument is ignored")

        try:
            database = self.client[target] if target else self.database
        except InvalidName as error:
            msg = "The target=`%s` is not a valid database name: %s"
            logger.error(msg, target, error)
            raise BackendParameterException(msg % (target, error)) from error

        try:
            for collection_info in database.list_collections():
                if details:
                    yield collection_info
                else:
                    yield collection_info.get("name")
        except PyMongoError as error:
            msg = "Failed to list MongoDB collections: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    @enforce_query_checks
    def read(
        self,
        *,
        query: Union[str, MongoQuery] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read documents matching the `query` from `target` collection and yield them.

        Args:
            query (str or MongoQuery): The MongoDB query to use when reading documents.
            target (str or None): The MongoDB collection name to query.
                If target is `None`, the `DEFAULT_COLLECTION` is used instead.
            chunk_size (int or None): The chunk size when reading archives by batch.
                If chunk_size is `None` the `DEFAULT_CHUNK_SIZE` is used instead.
            raw_output (bool): Whether to yield dictionaries or bytes.
            ignore_errors (bool): Whether to ignore errors when reading documents.

        Yields:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raises:
            BackendException: If a failure during the read operation occurs.
            BackendParameterException: If the `target` is not a valid collection name.
        """
        if not chunk_size:
            chunk_size = self.settings.DEFAULT_CHUNK_SIZE

        query = (query.query_string if query.query_string else query).dict(
            exclude={"query_string"}, exclude_unset=True
        )

        try:
            collection = self.database[target] if target else self.collection
        except InvalidName as error:
            msg = "The target=`%s` is not a valid collection name: %s"
            logger.error(msg, target, error)
            raise BackendParameterException(msg % (target, error)) from error

        try:
            documents = collection.find(batch_size=chunk_size, **query)
            documents = (d.update({"_id": str(d.get("_id"))}) or d for d in documents)
            if raw_output:
                documents = read_raw(
                    documents, self.settings.LOCALE_ENCODING, ignore_errors, logger
                )
            for document in documents:
                yield document
        except (PyMongoError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute MongoDB query: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
    ) -> int:
        """Write `data` documents to the `target` collection and return their count.

        Args:
            data (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target MongoDB collection name.
            chunk_size (int or None): The number of documents to write in one batch.
                If chunk_size is `None` the `DEFAULT_CHUNK_SIZE` is used instead.
            ignore_errors (bool): Whether to ignore errors or not.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                    instead. See `BaseOperationType`.

        Returns:
            int: The number of documents written.

        Raises:
            BackendException: If a failure occurs while writing to MongoDB or
                during document decoding and `ignore_errors` is set to `False`.
            BackendParameterException: If the `operation_type` is `APPEND` as it is not
                supported.
        """
        if not operation_type:
            operation_type = self.default_operation_type

        if operation_type == BaseOperationType.APPEND:
            msg = "Append operation_type is not allowed."
            logger.error(msg)
            raise BackendParameterException(msg)

        if not chunk_size:
            chunk_size = self.settings.DEFAULT_CHUNK_SIZE

        collection = self.database[target] if target else self.collection
        logger.debug(
            "Start writing to the %s collection of the %s database (chunk size: %d)",
            collection,
            self.database,
            chunk_size,
        )

        count = 0
        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return count
        data = chain([first_record], data)
        if isinstance(first_record, bytes):
            data = parse_bytes_to_dict(data, ignore_errors, logger)

        if operation_type == BaseOperationType.UPDATE:
            for batch in self.iter_by_batch(self.to_replace_one(data), chunk_size):
                count += self._bulk_update(batch, ignore_errors, collection)
            logger.info("Updated %d documents with success", count)
        elif operation_type == BaseOperationType.DELETE:
            for batch in self.iter_by_batch(self.to_ids(data), chunk_size):
                count += self._bulk_delete(batch, ignore_errors, collection)
            logger.info("Deleted %d documents with success", count)
        else:
            data = self.to_documents(data, ignore_errors, operation_type, logger)
            for batch in self.iter_by_batch(data, chunk_size):
                count += self._bulk_import(batch, ignore_errors, collection)
            logger.info("Inserted %d documents with success", count)

        return count

    def close(self) -> None:
        """Close the MongoDB backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        try:
            self.client.close()
        except PyMongoError as error:
            msg = "Failed to close MongoDB client: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    @staticmethod
    def iter_by_batch(data: Iterable[dict], chunk_size: int):
        """Iterate over `data` Iterable and yield batches of size `chunk_size`."""
        batch = []
        for document in data:
            batch.append(document)
            if len(batch) >= chunk_size:
                yield batch
                batch = []
        if batch:
            yield batch

    @staticmethod
    def to_ids(data: Iterable[dict]) -> Iterable[str]:
        """Convert `data` statements to ids."""
        for statement in data:
            yield statement.get("id")

    @staticmethod
    def to_replace_one(data: Iterable[dict]) -> Iterable[ReplaceOne]:
        """Convert `data` statements to Mongo `ReplaceOne` objects."""
        for statement in data:
            yield ReplaceOne(
                {"_source.id": {"$eq": statement.get("id")}},
                {"_source": statement},
            )

    @staticmethod
    def to_documents(
        data: Iterable[dict],
        ignore_errors: bool,
        operation_type: BaseOperationType,
        logger_class: logging.Logger,
    ) -> Generator[dict, None, None]:
        """Convert `data` statements to MongoDB documents.

        We expect statements to have at least an `id` and a `timestamp` field that will
        be used to compute a unique MongoDB Object ID. This ensures that we will not
        duplicate statements in our database and allows us to support pagination.
        """
        for statement in data:
            if "id" not in statement and operation_type == BaseOperationType.INDEX:
                msg = "statement %s has no 'id' field"
                if ignore_errors:
                    logger_class.warning("statement %s has no 'id' field", statement)
                    continue
                logger_class.error(msg, statement)
                raise BackendException(msg % statement)
            if "timestamp" not in statement:
                msg = "statement %s has no 'timestamp' field"
                if ignore_errors:
                    logger_class.warning(msg, statement)
                    continue
                logger_class.error(msg, statement)
                raise BackendException(msg % statement)
            try:
                timestamp = int(isoparse(statement["timestamp"]).timestamp())
            except ValueError as err:
                msg = "statement %s has an invalid 'timestamp' field"
                if ignore_errors:
                    logger_class.warning(msg, statement)
                    continue
                logger_class.error(msg, statement)
                raise BackendException(msg % statement) from err
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

    @staticmethod
    def _bulk_import(batch: list, ignore_errors: bool, collection: Collection):
        """Insert a `batch` of documents into the MongoDB `collection`."""
        try:
            new_documents = collection.insert_many(batch)
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to insert document chunk: %s"
            if ignore_errors:
                logger.warning(msg, error)
                return getattr(error, "details", {}).get("nInserted", 0)
            logger.error(msg, error)
            raise BackendException(msg % error) from error

        inserted_count = len(new_documents.inserted_ids)
        logger.debug("Inserted %d documents chunk with success", inserted_count)
        return inserted_count

    @staticmethod
    def _bulk_delete(batch: list, ignore_errors: bool, collection: Collection):
        """Delete a `batch` of documents from the MongoDB `collection`."""
        try:
            deleted_documents = collection.delete_many({"_source.id": {"$in": batch}})
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to delete document chunk: %s"
            if ignore_errors:
                logger.warning(msg, error)
                return getattr(error, "details", {}).get("nRemoved", 0)
            logger.error(msg, error)
            raise BackendException(msg % error) from error

        deleted_count = deleted_documents.deleted_count
        logger.debug("Deleted %d documents chunk with success", deleted_count)
        return deleted_count

    @staticmethod
    def _bulk_update(batch: list, ignore_errors: bool, collection: Collection):
        """Update a `batch` of documents into the MongoDB `collection`."""
        try:
            updated_documents = collection.bulk_write(batch)
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to update document chunk: %s"
            if ignore_errors:
                logger.warning(msg, error)
                return getattr(error, "details", {}).get("nModified", 0)
            logger.error(msg, error)
            raise BackendException(msg % error) from error

        modified_count = updated_documents.modified_count
        logger.debug("Updated %d documents chunk with success", modified_count)
        return modified_count
