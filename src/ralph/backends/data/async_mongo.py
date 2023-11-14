"""Asynchronous MongoDB data backend for Ralph."""

from io import IOBase
from typing import AsyncIterator, Iterable, Optional, TypeVar, Union

from bson.errors import BSONError
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pydantic import PositiveInt
from pymongo.errors import BulkWriteError, ConnectionFailure, InvalidName, PyMongoError

from ralph.backends.data.base import BaseOperationType
from ralph.backends.data.mongo import (
    MongoDataBackend,
    MongoDataBackendSettings,
    MongoQuery,
)
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import async_parse_dict_to_bytes, iter_by_batch, parse_iterable_to_dict

from ..data.base import (
    AsyncListable,
    AsyncWritable,
    BaseAsyncDataBackend,
    DataBackendStatus,
)

Settings = TypeVar("Settings", bound=MongoDataBackendSettings)


class AsyncMongoDataBackend(
    BaseAsyncDataBackend[Settings, MongoQuery],
    AsyncWritable,
    AsyncListable,
):
    """Asynchronous MongoDB data backend."""

    name = "async_mongo"
    unsupported_operation_types = {BaseOperationType.APPEND}

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the asynchronous MongoDB client.

        Args:
            settings (MongoDataBackendSettings or None): The data backend settings.
        """
        super().__init__(settings)
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
            self.logger.error("Failed to connect to MongoDB: %s", error)
            return DataBackendStatus.AWAY

        # Check MongoDB server status.
        try:
            server_status = await self.client.admin.command("serverStatus")
            if server_status.get("ok") != 1.0:  # noqa: PLR2004
                self.logger.error("MongoDB `serverStatus` command did not return 1.0")
                return DataBackendStatus.ERROR
        except PyMongoError as error:
            self.logger.error("Failed to get MongoDB server status: %s", error)
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    async def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[AsyncIterator[str], AsyncIterator[dict]]:
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
            self.logger.warning("The `new` argument is ignored")

        try:
            database = self.client[target] if target else self.database
        except InvalidName as error:
            msg = "The target=`%s` is not a valid database name: %s"
            self.logger.error(msg, target, error)
            raise BackendParameterException(msg % (target, error)) from error

        try:
            collections = await database.list_collections()
            async for collection_info in collections:
                if details:
                    yield collection_info
                else:
                    yield collection_info.get("name")
        except PyMongoError as error:
            msg = "Failed to list MongoDB collections: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    async def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, MongoQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[AsyncIterator[bytes], AsyncIterator[dict]]:
        """Read documents matching the `query` from `target` collection and yield them.

        Args:
            query (str or MongoQuery): The MongoDB query to use when fetching documents.
            target (str or None): The MongoDB collection name to query.
                If target is `None`, the `DEFAULT_COLLECTION` is used instead.
            chunk_size (int or None): The chunk size when reading documents by batches.
                If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
            raw_output (bool): Whether to yield dictionaries or bytes.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default), there is no maximum.

        Yield:
            bytes: The next raw document if `raw_output` is True.
            dict: The next JSON parsed document if `raw_output` is False.

        Raise:
            BackendException: If a failure occurs during MongoDB connection or
                during encoding documents and `ignore_errors` is set to `False`.
            BackendParameterException: If the `target` is not a valid collection name.
        """
        statements = super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )
        async for statement in statements:
            yield statement

    async def _read_bytes(
        self,
        query: MongoQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
    ) -> AsyncIterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        statements = self._read_dicts(query, target, chunk_size, ignore_errors)
        async for statement in async_parse_dict_to_bytes(
            statements, self.settings.LOCALE_ENCODING, ignore_errors, self.logger
        ):
            yield statement

    async def _read_dicts(
        self,
        query: MongoQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> AsyncIterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        query = query.query_string if query.query_string else query
        query = query.dict(exclude={"query_string"}, exclude_unset=True)
        collection = self._get_target_collection(target)
        try:
            async for document in collection.find(batch_size=chunk_size, **query):
                document.update({"_id": str(document.get("_id"))})
                yield document
        except (PyMongoError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute MongoDB query: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    async def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
        simultaneous: bool = False,
        max_num_simultaneous: Optional[int] = None,
    ) -> int:
        """Write data documents to the target collection and return their count.

        Args:
            data (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target MongoDB collection name.
            chunk_size (int or None): The number of documents to write in one batch.
                If `chunk_size` is `None` it defaults to `WRITE_CHUNK_SIZE`.
            ignore_errors (bool): If `True`, errors during decoding, encoding and
                sending batches of documents are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                    instead. See `BaseOperationType`.
            simultaneous (bool): If `True`, chunks will be written concurrently.
                If `False` (default), chunks will be written sequentially.
            max_num_simultaneous (int or None): If simultaneous is `True`, the maximum
                number of chunks to write concurrently. If `None` it defaults to 1.

        Return:
            int: The number of documents written.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If the `operation_type` is `APPEND` as it is not
                supported.
        """
        return await super().write(
            data,
            target,
            chunk_size,
            ignore_errors,
            operation_type,
            simultaneous,
            max_num_simultaneous,
        )

    async def _write_bytes(  # noqa: PLR0913
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        statements = parse_iterable_to_dict(data, ignore_errors, self.logger)
        return await self._write_dicts(
            statements, target, chunk_size, ignore_errors, operation_type
        )

    async def _write_dicts(  # noqa: PLR0913
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
            data = MongoDataBackend.to_replace_one(data)
            for batch in iter_by_batch(data, chunk_size):
                count += await self._bulk_update(batch, ignore_errors, collection)
            self.logger.info("Updated %d documents with success", count)
        elif operation_type == BaseOperationType.DELETE:
            for batch in iter_by_batch(MongoDataBackend.to_ids(data), chunk_size):
                count += await self._bulk_delete(batch, ignore_errors, collection)
            self.logger.info("Deleted %d documents with success", count)
        else:
            data = MongoDataBackend.to_documents(
                data, ignore_errors, operation_type, self.logger
            )
            for batch in iter_by_batch(data, chunk_size):
                count += await self._bulk_import(batch, ignore_errors, collection)
            self.logger.info("Inserted %d documents with success", count)

        return count

    async def close(self) -> None:
        """Close the AsyncIOMotorClient client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        try:
            self.client.close()
        except PyMongoError as error:
            msg = "Failed to close AsyncIOMotorClient: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    def _get_target_collection(
        self, target: Union[str, None]
    ) -> AsyncIOMotorCollection:
        """Return the target collection."""
        try:
            return self.database[target] if target else self.collection
        except InvalidName as error:
            msg = "The target=`%s` is not a valid collection name: %s"
            self.logger.error(msg, target, error)
            raise BackendParameterException(msg % (target, error)) from error

    async def _bulk_import(
        self, batch: list, ignore_errors: bool, collection: AsyncIOMotorCollection
    ):
        """Insert a batch of documents into the selected database collection."""
        try:
            new_documents = await collection.insert_many(batch)
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to insert document chunk: %s"
            if ignore_errors:
                self.logger.warning(msg, error)
                return getattr(error, "details", {}).get("nInserted", 0)
            raise BackendException(msg % error) from error

        inserted_count = len(new_documents.inserted_ids)
        self.logger.debug("Inserted %d documents chunk with success", inserted_count)
        return inserted_count

    async def _bulk_delete(
        self, batch: list, ignore_errors: bool, collection: AsyncIOMotorCollection
    ):
        """Delete a batch of documents from the selected database collection."""
        try:
            deleted_documents = await collection.delete_many(
                {"_source.id": {"$in": batch}}
            )
        except (BulkWriteError, PyMongoError, BSONError, ValueError) as error:
            msg = "Failed to delete document chunk: %s"
            if ignore_errors:
                self.logger.warning(msg, error)
                return getattr(error, "details", {}).get("nRemoved", 0)
            raise BackendException(msg % error) from error

        deleted_count = deleted_documents.deleted_count
        self.logger.debug("Deleted %d documents chunk with success", deleted_count)
        return deleted_count

    async def _bulk_update(
        self, batch: list, ignore_errors: bool, collection: AsyncIOMotorCollection
    ):
        """Update a batch of documents into the selected database collection."""
        try:
            updated_documents = await collection.bulk_write(batch)
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
