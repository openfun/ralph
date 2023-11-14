"""MongoDB data backend for Ralph."""

from __future__ import annotations

import hashlib
import logging
import struct
from io import IOBase
from typing import Generator, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union
from uuid import uuid4

from bson.errors import BSONError
from bson.objectid import ObjectId
from dateutil.parser import isoparse
from pydantic import Json, MongoDsn, PositiveInt, constr
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
    Listable,
    Writable,
)
from ralph.conf import BaseSettingsConfig, ClientOptions
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import iter_by_batch, parse_dict_to_bytes, parse_iterable_to_dict


class MongoClientOptions(ClientOptions):
    """MongoDB additional client options."""

    document_class: Optional[str] = None
    tz_aware: Optional[bool] = None


class MongoDataBackendSettings(BaseDataBackendSettings):
    """MongoDB data backend default configuration.

    Attributes:
        CONNECTION_URI (str): The MongoDB connection URI.
        DEFAULT_DATABASE (str): The MongoDB database to connect to.
        DEFAULT_COLLECTION (str): The MongoDB database collection to get objects from.
        CLIENT_OPTIONS (MongoClientOptions): A dictionary of MongoDB client options.
        LOCALE_ENCODING (str): The locale encoding to use when none is provided.
        READ_CHUNK_SIZE (int): The default chunk size for reading batches of documents.
        WRITE_CHUNK_SIZE (int): The default chunk size for writing batches of documents.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__MONGO__"

    CONNECTION_URI: MongoDsn = MongoDsn("mongodb://localhost:27017/", scheme="mongodb")
    DEFAULT_DATABASE: constr(regex=r"^[^\s.$/\\\"\x00]+$") = "statements"
    DEFAULT_COLLECTION: constr(
        regex=r"^(?!.*\.\.)[^.$\x00]+(?:\.[^.$\x00]+)*$"
    ) = "marsha"
    CLIENT_OPTIONS: MongoClientOptions = MongoClientOptions()


class BaseMongoQuery(BaseQuery):
    """Base MongoDB query model."""

    filter: Union[dict, None]
    limit: Union[int, None]
    projection: Union[dict, None]
    sort: Union[List[Tuple], None]


class MongoQuery(BaseMongoQuery):
    """MongoDB query model."""

    query_string: Union[Json[BaseMongoQuery], None]


Settings = TypeVar("Settings", bound=MongoDataBackendSettings)


class MongoDataBackend(BaseDataBackend[Settings, MongoQuery], Writable, Listable):
    """MongoDB data backend."""

    name = "mongo"
    unsupported_operation_types = {BaseOperationType.APPEND}

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the MongoDB client.

        Args:
            settings (MongoDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self.client = MongoClient(
            self.settings.CONNECTION_URI, **self.settings.CLIENT_OPTIONS.dict()
        )
        self.database = self.client[self.settings.DEFAULT_DATABASE]
        self.collection = self.database[self.settings.DEFAULT_COLLECTION]

    def status(self) -> DataBackendStatus:
        """Check the MongoDB connection status.

        Return:
            DataBackendStatus: The status of the data backend.
        """
        # Check MongoDB connection.
        try:
            self.client.admin.command("ping")
        except (ConnectionFailure, InvalidOperation) as error:
            self.logger.error("Failed to connect to MongoDB: %s", error)
            return DataBackendStatus.AWAY

        # Check MongoDB server status.
        try:
            if (
                self.client.admin.command("serverStatus").get("ok")
                != 1.0  # noqa: PLR2004
            ):
                self.logger.error("MongoDB `serverStatus` command did not return 1.0")
                return DataBackendStatus.ERROR
        except PyMongoError as error:
            self.logger.error("Failed to get MongoDB server status: %s", error)
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
        """List collections in the `target` database.

        Args:
            target (str or None): The MongoDB database name to list collections from.
                If target is `None`, the `DEFAULT_DATABASE` is used instead.
            details (bool): Get detailed collection information instead of just IDs.
            new (bool): Ignored.

        Raise:
            BackendException: If a failure during the list operation occurs.
            BackendParameterException: If the `target` is not a valid database name.
        """
        if new:
            self.logger.warning("The `new` argument is ignored")

        try:
            database = self.client[target] if target else self.database
        except InvalidName as error:
            msg = "The target=`%s` is not a valid database name: %s"
            self.logger.error(msg, target, error)
            raise BackendParameterException(msg % (target, error)) from error

        try:
            for collection_info in database.list_collections():
                if details:
                    yield collection_info
                else:
                    yield collection_info.get("name")
        except PyMongoError as error:
            msg = "Failed to list MongoDB collections: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, MongoQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        greedy: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
        """Read documents matching the `query` from `target` collection and yield them.

        Args:
            query (str or MongoQuery): The MongoDB query to use when reading documents.
            target (str or None): The MongoDB collection name to query.
                If target is `None`, the `DEFAULT_COLLECTION` is used instead.
            chunk_size (int or None): The chunk size when reading archives by batch.
                If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
            raw_output (bool): Whether to yield dictionaries or bytes.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            greedy: If set to `True`, the client will fetch all available records
                before they are yielded by the generator. Caution:
                this might potentially lead to large amounts of API calls and to the
                memory filling up.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default), there is no maximum.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure occurs during MongoDB connection or
                during encoding documents and `ignore_errors` is set to `False`.
            BackendParameterException: If the `target` is not a valid collection name.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, greedy, max_statements
        )

    def _read_bytes(
        self,
        query: MongoQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        locale = self.settings.LOCALE_ENCODING
        statements = self._read_dicts(query, target, chunk_size, ignore_errors)
        yield from parse_dict_to_bytes(statements, locale, ignore_errors, self.logger)

    def _read_dicts(
        self,
        query: MongoQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        query = query.query_string if query.query_string else query
        query = query.dict(exclude={"query_string"}, exclude_unset=True)
        collection = self._get_target_collection(target)
        try:
            documents = collection.find(batch_size=chunk_size, **query)
            yield from (d.update({"_id": str(d.get("_id"))}) or d for d in documents)
        except (PyMongoError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute MongoDB query: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` documents to the `target` collection and return their count.

        Args:
            data (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target MongoDB collection name.
            chunk_size (int or None): The number of documents to write in one batch.
                If `chunk_size` is `None` it defaults to `WRITE_CHUNK_SIZE`.
            ignore_errors (bool):  If `True`, errors during decoding, encoding and
                sending batches of documents are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                    instead. See `BaseOperationType`.

        Return:
            int: The number of documents written.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If the `operation_type` is `APPEND` as it is not
                supported.
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_bytes(  # noqa: PLR0913
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        statements = parse_iterable_to_dict(data, ignore_errors, self.logger)
        return self._write_dicts(
            statements, target, chunk_size, ignore_errors, operation_type
        )

    def _write_dicts(  # noqa: PLR0913
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        count = 0
        collection = self._get_target_collection(target)
        msg = "Start writing to the %s collection of the %s database (chunk size: %d)"
        self.logger.debug(msg, collection, self.database, chunk_size)
        if operation_type == BaseOperationType.UPDATE:
            for batch in iter_by_batch(self.to_replace_one(data), chunk_size):
                count += self._bulk_update(batch, ignore_errors, collection)
            self.logger.info("Updated %d documents with success", count)
        elif operation_type == BaseOperationType.DELETE:
            for batch in iter_by_batch(self.to_ids(data), chunk_size):
                count += self._bulk_delete(batch, ignore_errors, collection)
            self.logger.info("Deleted %d documents with success", count)
        else:
            data = self.to_documents(data, ignore_errors, operation_type, self.logger)
            for batch in iter_by_batch(data, chunk_size):
                count += self._bulk_import(batch, ignore_errors, collection)
            self.logger.info("Inserted %d documents with success", count)

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
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

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
        logger: logging.Logger,
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
                    logger.warning("statement %s has no 'id' field", statement)
                    continue
                logger.error(msg, statement)
                raise BackendException(msg % statement)
            if "timestamp" not in statement:
                msg = "statement %s has no 'timestamp' field"
                if ignore_errors:
                    logger.warning(msg, statement)
                    continue
                logger.error(msg, statement)
                raise BackendException(msg % statement)
            try:
                timestamp = int(isoparse(statement["timestamp"]).timestamp())
            except ValueError as err:
                msg = "statement %s has an invalid 'timestamp' field"
                if ignore_errors:
                    logger.warning(msg, statement)
                    continue
                logger.error(msg, statement)
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

    def _get_target_collection(self, target: Union[str, None]) -> Collection:
        """Return the validated target collection."""
        try:
            return self.database[target] if target else self.collection
        except InvalidName as error:
            msg = "The target=`%s` is not a valid collection name: %s"
            self.logger.error(msg, target, error)
            raise BackendParameterException(msg % (target, error)) from error

    def _bulk_import(
        self, batch: List, ignore_errors: bool, collection: Collection
    ) -> int:
        """Insert a `batch` of documents into the MongoDB `collection`."""
        try:
            new_documents = collection.insert_many(batch)
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to insert document chunk: %s"
            if ignore_errors:
                self.logger.warning(msg, error)
                return getattr(error, "details", {}).get("nInserted", 0)
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

        inserted_count = len(new_documents.inserted_ids)
        self.logger.debug("Inserted %d documents chunk with success", inserted_count)
        return inserted_count

    def _bulk_delete(
        self, batch: List, ignore_errors: bool, collection: Collection
    ) -> int:
        """Delete a `batch` of documents from the MongoDB `collection`."""
        try:
            deleted_documents = collection.delete_many({"_source.id": {"$in": batch}})
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to delete document chunk: %s"
            if ignore_errors:
                self.logger.warning(msg, error)
                return getattr(error, "details", {}).get("nRemoved", 0)
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

        deleted_count = deleted_documents.deleted_count
        self.logger.debug("Deleted %d documents chunk with success", deleted_count)
        return deleted_count

    def _bulk_update(
        self, batch: List, ignore_errors: bool, collection: Collection
    ) -> int:
        """Update a `batch` of documents into the MongoDB `collection`."""
        try:
            updated_documents = collection.bulk_write(batch)
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to update document chunk: %s"
            if ignore_errors:
                self.logger.warning(msg, error)
                return getattr(error, "details", {}).get("nModified", 0)
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

        modified_count = updated_documents.modified_count
        self.logger.debug("Updated %d documents chunk with success", modified_count)
        return modified_count
