"""Async MongoDB data backend for Ralph."""

import json
import logging
from io import IOBase
from itertools import chain
from typing import Any, Dict, Iterable, Iterator, Union

from bson.errors import BSONError
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, ConnectionFailure, InvalidName, PyMongoError

from ralph.backends.data.base import BaseOperationType
from ralph.backends.data.mongo import (
    MongoDataBackend,
    MongoDataBackendSettings,
    MongoQuery,
)
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import parse_bytes_to_dict

from ..data.base import BaseAsyncDataBackend, DataBackendStatus, enforce_query_checks

logger = logging.getLogger(__name__)


class AsyncMongoDataBackend(BaseAsyncDataBackend):
    """Async MongoDB data backend."""

    name = "async_mongo"
    query_model = MongoQuery
    settings_class = MongoDataBackendSettings

    def __init__(self, settings: Union[settings_class, None] = None):
        """Instantiate the asynchronous MongoDB client.

        Args:
            settings (MongoDataBackendSettings or None): The data backend settings.
        """
        self.settings = settings if settings else self.settings_class()
        self.client = AsyncIOMotorClient(
            self.settings.CONNECTION_URI, **self.settings.CLIENT_OPTIONS.dict()
        )
        self.database = self.client[self.settings.DEFAULT_DATABASE]
        self.collection = self.database[self.settings.DEFAULT_COLLECTION]

    async def status(self) -> DataBackendStatus:
        """Check the MongoDB connection status.

        Return:
            DataBackendStatus: The status of the data backend.
        """
        # Check MongoDB connection.
        try:
            await self.client.admin.command("ping")
        except (ConnectionFailure, PyMongoError) as error:
            logger.error("Failed to connect to MongoDB: %s", error)
            return DataBackendStatus.AWAY

        # Check MongoDB server status.
        try:
            if (await self.client.admin.command("serverStatus")).get("ok") != 1.0:
                logger.error("MongoDB `serverStatus` command did not return 1.0")
                return DataBackendStatus.ERROR
        except PyMongoError as error:
            logger.error("Failed to get MongoDB server status: %s", error)
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    async def list(
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List collections in the target database.

        Args:
            target (str or None): The MongoDB database name to list collections from.
                If target is `None`, the `DEFAULT_DATABASE` is used instead.
            details (bool): Get detailed collection information instead of just IDs.
            new (bool): Ignored.

        Yield:
            str: The next collection. (If `details` is False).
            dict: The next collection details. (If `details` is True).

        Raise:
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
            collections = await database.list_collections()
            for collection_info in collections:
                if details:
                    yield collection_info
                else:
                    yield collection_info.get("name")
        except PyMongoError as error:
            msg = "Failed to list MongoDB collections: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    @enforce_query_checks
    async def read(
        self,
        *,
        query: Union[str, MongoQuery] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Read documents matching the `query` from `target` collection and yield them.

        Args:
            query (str or MongoQuery): The MongoDB query to use when fetching documents.
            target (str or None): The MongoDB collection name to query.
                If target is `None`, the `DEFAULT_COLLECTION` is used instead.
            chunk_size (int or None): The chunk size when reading documents by batches.
                If chunk_size is `None` the `DEFAULT_CHUNK_SIZE` is used instead.
            raw_output (bool): Whether to yield dictionaries or bytes.
            ignore_errors (bool): Whether to ignore errors when reading documents.

        Yield:
            bytes: The next raw document if `raw_output` is True.
            dict: The next JSON parsed document if `raw_output` is False.

        Raise:
            BackendException: If a failure occurs during MongoDB connection.
            BackendParameterException: If a failure occurs with MongoDB collection.
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

        reader = self._read_raw if raw_output else lambda _: _
        try:
            async for document in collection.find(batch_size=chunk_size, **query):
                document.update({"_id": str(document.get("_id"))})
                try:
                    yield reader(document)
                except (TypeError, ValueError) as error:
                    msg = "Failed to encode MongoDB document with ID %s: %s"
                    document_id = document.get("_id")
                    logger.error(msg, document_id, error)
                    if ignore_errors:
                        logger.warning(msg, document_id, error)
                        continue
                    raise BackendException(msg % (document_id, error)) from error
        except (PyMongoError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute MongoDB query: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    async def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
    ) -> int:
        """Write data documents to the target collection and return their count.

        Args:
            data (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target MongoDB collection name.
            chunk_size (int or None): The number of documents to write in one batch.
                If chunk_size is `None` the `DEFAULT_CHUNK_SIZE` is used instead.
            ignore_errors (bool): Whether to ignore errors or not.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                    instead. See `BaseOperationType`.

        Return:
            int: The number of documents written.

        Raise:
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
            logger.warning("Data Iterator is empty; skipping write to target.")
            return count
        data = chain([first_record], data)
        if isinstance(first_record, bytes):
            data = parse_bytes_to_dict(data, ignore_errors, logger)

        if operation_type == BaseOperationType.UPDATE:
            for batch in MongoDataBackend.iter_by_batch(
                MongoDataBackend.to_replace_one(data), chunk_size
            ):
                count += await self._bulk_update(batch, ignore_errors, collection)
            logger.info("Updated %d documents with success", count)
        elif operation_type == BaseOperationType.DELETE:
            for batch in MongoDataBackend.iter_by_batch(
                MongoDataBackend.to_ids(data), chunk_size
            ):
                count += await self._bulk_delete(batch, ignore_errors, collection)
            logger.info("Deleted %d documents with success", count)
        else:
            data = MongoDataBackend.to_documents(
                data, ignore_errors, operation_type, logger
            )
            for batch in MongoDataBackend.iter_by_batch(data, chunk_size):
                count += await self._bulk_import(batch, ignore_errors, collection)
            logger.info("Inserted %d documents with success", count)

        return count

    async def close(self) -> None:
        """Close the AsyncIOMotorClient client.

        Raise:
            BackendException: If a failure during the close operation occurs.
        """
        try:
            self.client.close()
        except PyMongoError as error:
            msg = "Failed to close AsyncIOMotorClient: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    @staticmethod
    async def _bulk_import(batch: list, ignore_errors: bool, collection: Collection):
        """Insert a batch of documents into the selected database collection."""
        try:
            new_documents = await collection.insert_many(batch)
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to insert document chunk: %s"
            if ignore_errors:
                logger.warning(msg, error)
                return getattr(error, "details", {}).get("nInserted", 0)
            raise BackendException(msg % error) from error

        inserted_count = len(new_documents.inserted_ids)
        logger.debug("Inserted %d documents chunk with success", inserted_count)
        return inserted_count

    @staticmethod
    async def _bulk_delete(batch: list, ignore_errors: bool, collection: Collection):
        """Delete a batch of documents from the selected database collection."""
        try:
            deleted_documents = await collection.delete_many(
                {"_source.id": {"$in": batch}}
            )
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to delete document chunk: %s"
            if ignore_errors:
                logger.warning(msg, error)
                return getattr(error, "details", {}).get("nRemoved", 0)
            raise BackendException(msg % error) from error

        deleted_count = deleted_documents.deleted_count
        logger.debug("Deleted %d documents chunk with success", deleted_count)
        return deleted_count

    @staticmethod
    async def _bulk_update(batch: list, ignore_errors: bool, collection: Collection):
        """Update a batch of documents into the selected database collection."""
        try:
            updated_documents = await collection.bulk_write(batch)
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

    def _read_raw(self, document: Dict[str, Any]) -> bytes:
        """Read the `document` dictionary and return bytes."""
        return json.dumps(document).encode(self.settings.LOCALE_ENCODING)
