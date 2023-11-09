"""ClickHouse data backend for Ralph."""

import json
import logging
from datetime import datetime
from io import IOBase
from itertools import chain
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Union,
)
from uuid import UUID, uuid4

import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError
from pydantic import BaseModel, ValidationError

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    DataBackendStatus,
    Listable,
    Writable,
)
from ralph.conf import BaseSettingsConfig, ClientOptions
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class ClickHouseInsert(BaseModel):
    """Model to validate required fields for ClickHouse insertion."""

    event_id: UUID
    emission_time: datetime


class ClickHouseClientOptions(ClientOptions):
    """Pydantic model for `clickhouse` client options."""

    date_time_input_format: str = "best_effort"


class InsertTuple(NamedTuple):
    """Named tuple for ClickHouse insertion."""

    event_id: UUID
    emission_time: datetime
    event: str


class ClickHouseDataBackendSettings(BaseDataBackendSettings):
    """Represent the ClickHouse data backend default configuration.

    Attributes:
        HOST (str): ClickHouse server host to connect to.
        PORT (int): ClickHouse server port to connect to.
        DATABASE (str): ClickHouse database to connect to.
        EVENT_TABLE_NAME (str): Table where events live.
        USERNAME (str): ClickHouse username to connect as (optional).
        PASSWORD (str): Password for the given ClickHouse username (optional).
        CLIENT_OPTIONS (ClickHouseClientOptions): A dictionary of valid options for the
            ClickHouse client connection.
        DEFAULT_CHUNK_SIZE (int): The default chunk size for reading/writing.
        LOCALE_ENCODING (str): The locale encoding to use when none is provided.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__CLICKHOUSE__"

    HOST: str = "localhost"
    PORT: int = 8123
    DATABASE: str = "xapi"
    EVENT_TABLE_NAME: str = "xapi_events_all"
    USERNAME: str = None
    PASSWORD: str = None
    CLIENT_OPTIONS: ClickHouseClientOptions = ClickHouseClientOptions()
    DEFAULT_CHUNK_SIZE: int = 500
    LOCALE_ENCODING: str = "utf8"


class ClickHouseQuery(BaseModel):
    """Base ClickHouse query model.

    Attributes:
        select:
        where:
        parameters:
        limit:
        sort:
        column_oriented:
    """

    select: Union[str, List[str]] = "event"
    where: Union[str, List[str], None]
    parameters: Union[Dict, None]
    limit: Union[int, None]
    sort: Union[str, None]
    column_oriented: Union[bool, None] = False


class ClickHouseDataBackend(BaseDataBackend, Writable, Listable):
    """ClickHouse database backend."""

    name = "clickhouse"
    query_class = ClickHouseQuery
    default_operation_type = BaseOperationType.CREATE
    settings_class = ClickHouseDataBackendSettings

    def __init__(self, settings: Optional[ClickHouseDataBackendSettings] = None):
        """Instantiate the ClickHouse configuration.

        Args:
            settings (ClickHouseDataBackendSettings or None): The ClickHouse
                data backend settings.
        """
        self.settings = settings if settings else self.settings_class()
        self.database = self.settings.DATABASE
        self.event_table_name = self.settings.EVENT_TABLE_NAME
        self.default_chunk_size = self.settings.DEFAULT_CHUNK_SIZE
        self.locale_encoding = self.settings.LOCALE_ENCODING
        self._client = None

    @property
    def client(self):
        """Create a ClickHouse client if it doesn't exist.

        We do this here so that we don't interrupt initialization in the case
        where ClickHouse is not running when Ralph starts up, which will cause
        Ralph to hang. This client is HTTP, so not actually stateful. Ralph
        should be able to gracefully deal with ClickHouse outages at all other
        times.
        """
        if not self._client:
            self._client = clickhouse_connect.get_client(
                host=self.settings.HOST,
                port=self.settings.PORT,
                database=self.database,
                username=self.settings.USERNAME,
                password=self.settings.PASSWORD,
                settings=self.settings.CLIENT_OPTIONS.dict(),
            )
        return self._client

    def status(self) -> DataBackendStatus:
        """Check ClickHouse connection status.

        Return:
            DataBackendStatus: The status of the data backend.
        """
        try:
            self.client.query("SELECT 1")
        except ClickHouseError:
            return DataBackendStatus.AWAY

        return DataBackendStatus.OK

    def list(
        self,
        target: Optional[str] = None,
        details: bool = False,
        new: bool = False,  # noqa: ARG002
    ) -> Iterator[Union[str, dict]]:
        """List tables for a given database.

        Args:
            target (str): The database name to list tables from.
            details (bool): Get detailed table information instead of just ids.
            new (bool): Given the history, list only not already fetched archives.

        Yield:
            str: The next table name. (If `details` is False).
            dict: The next table name. (If `details` is True).

        Raise:
            BackendException: If a failure during table names retrieval occurs.
        """
        sql = f"SHOW TABLES FROM {target if target else self.database}"

        try:
            tables = self.client.query(sql).named_results()
        except (ClickHouseError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to read tables: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

        for table in tables:
            if details:
                yield table
            else:
                yield str(table.get("name"))

    def read(  # noqa: PLR0912, PLR0913
        self,
        *,
        query: Optional[ClickHouseQuery] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Read documents matching the query in the target table and yield them.

        Args:
            query (ClickHouseQuery): The query to use when fetching documents.
            target (str or None): The target table name to query.
                If target is `None`, the `event_table_name` is used instead.
            chunk_size (int or None): The chunk size when reading documents by batches.
                If chunk_size is `None` it defaults to `default_chunk_size`.
            raw_output (bool): Controls whether to yield dictionaries or bytes.
            ignore_errors (bool): If `True`, errors during the encoding operation
                will be ignored and logged. If `False` (default), a `BackendException`
                will be raised if an error occurs.

        Yield:
            bytes: The next raw document if `raw_output` is True.
            dict: The next JSON parsed document if `raw_output` is False.

        Raise:
            BackendException: If a failure occurs during ClickHouse connection.
        """
        if target is None:
            target = self.event_table_name

        if chunk_size is None:
            chunk_size = self.default_chunk_size

        if query is None:
            query = self.query_class()

        if isinstance(query.select, str):
            query.select = [query.select]
        select = ",".join(query.select)
        sql = f"SELECT {select} FROM {target}"  # noqa: S608

        if query.where:
            if isinstance(query.where, str):
                query.where = [query.where]
            filter_str = "\nWHERE 1=1 AND "
            filter_str += """
            AND
            """.join(
                query.where
            )
            sql += filter_str

        if query.sort:
            sql += f"\nORDER BY {query.sort}"

        if query.limit:
            sql += f"\nLIMIT {query.limit}"

        reader = self._read_raw if raw_output else self._read_json

        logger.debug(
            "Start reading the %s table of the %s database (chunk size: %d)",
            target,
            self.database,
            chunk_size,
        )
        try:
            result = self.client.query(
                sql,
                parameters=query.parameters,
                settings={"buffer_size": chunk_size},
                column_oriented=query.column_oriented,
            ).named_results()
            for statement in result:
                try:
                    yield reader(statement)
                except (TypeError, ValueError) as error:
                    msg = "Failed to encode document %s: %s"
                    if ignore_errors:
                        logger.warning(msg, statement, error)
                        continue
                    logger.error(msg, statement, error)
                    raise BackendException(msg % (statement, error)) from error
        except (ClickHouseError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to read documents: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` documents to the `target` table and return their count.

        Args:
            data: (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target table name.
                If target is `None`, the `event_table_name` is used instead.
            chunk_size (int or None): The number of documents to write in one batch.
                If `chunk_size` is `None` it defaults to `default_chunk_size`.
            ignore_errors (bool): If `True`, errors during the write operation
                will be ignored and logged. If `False` (default), a `BackendException`
                will be raised if an error occurs.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.

        Return:
            int: The number of documents written.

        Raise:
            BackendException: If a failure occurs while writing to ClickHouse or
                during document decoding and `ignore_errors` is set to `False`.
            BackendParameterException: If the `operation_type` is `APPEND`, `UPDATE`
                or `DELETE` as it is not supported.
        """
        target = target if target else self.event_table_name
        if not operation_type:
            operation_type = self.default_operation_type
        if not chunk_size:
            chunk_size = self.default_chunk_size
        logger.debug(
            "Start writing to the %s table of the %s database (chunk size: %d)",
            target,
            self.database,
            chunk_size,
        )

        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return 0

        data = chain([first_record], data)
        if isinstance(first_record, bytes):
            data = self._parse_bytes_to_dict(data, ignore_errors)

        if operation_type not in [BaseOperationType.CREATE, BaseOperationType.INDEX]:
            msg = "%s operation_type is not allowed."
            logger.error(msg, operation_type.name)
            raise BackendParameterException(msg % operation_type.name)

        # operation_type is either CREATE or INDEX
        count = 0
        batch = []

        for insert_tuple in self._to_insert_tuples(
            data,
            ignore_errors=ignore_errors,
        ):
            batch.append(insert_tuple)
            if len(batch) < chunk_size:
                continue

            count += self._bulk_import(
                batch,
                ignore_errors=ignore_errors,
                event_table_name=target,
            )
            batch = []

        # Edge case: if the total number of documents is lower than the chunk size
        if len(batch) > 0:
            count += self._bulk_import(
                batch,
                ignore_errors=ignore_errors,
                event_table_name=target,
            )

        logger.info("Inserted a total of %d documents with success", count)

        return count

    def close(self) -> None:
        """Close the ClickHouse backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            logger.warning("No backend client to close.")
            return

        try:
            self.client.close()
        except ClickHouseError as error:
            msg = "Failed to close ClickHouse client: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    @staticmethod
    def _to_insert_tuples(
        data: Iterable[dict],
        ignore_errors: bool = False,
    ) -> Generator[InsertTuple, None, None]:
        """Convert `data` dictionaries to insert tuples."""
        for statement in data:
            try:
                insert = ClickHouseInsert(
                    event_id=statement.get("id", str(uuid4())),
                    emission_time=statement["timestamp"],
                )
            except (KeyError, ValidationError) as error:
                msg = "Statement %s has an invalid 'id' or 'timestamp' field"
                if ignore_errors:
                    logger.warning(msg, statement)
                    continue
                logger.error(msg, statement)
                raise BackendException(msg % statement) from error

            insert_tuple = InsertTuple(
                insert.event_id,
                insert.emission_time,
                json.dumps(statement),
            )

            yield insert_tuple

    def _bulk_import(
        self,
        batch: list,
        ignore_errors: bool = False,
        event_table_name: Optional[str] = None,
    ):
        """Insert a batch of documents into the selected database table."""
        try:
            found_ids = {document.event_id for document in batch}

            if len(found_ids) != len(batch):
                raise BackendException("Duplicate IDs found in batch")

            self.client.insert(
                event_table_name,
                batch,
                column_names=["event_id", "emission_time", "event"],
                # Allow ClickHouse to buffer the insert, and wait for the
                # buffer to flush. Should be configurable, but I think these are
                # reasonable defaults.
                settings={"async_insert": 1, "wait_for_async_insert": 1},
            )
        except (ClickHouseError, BackendException) as error:
            if not ignore_errors:
                raise BackendException(*error.args) from error
            logger.warning(
                "Bulk import failed for current chunk but you choose to ignore it.",
            )
            # There is no current way of knowing how many rows from the batch
            # succeeded, we assume 0 here.
            return 0

        inserted_count = len(batch)
        logger.debug("Inserted %d documents chunk with success", inserted_count)

        return inserted_count

    @staticmethod
    def _parse_bytes_to_dict(
        raw_documents: Iterable[bytes], ignore_errors: bool
    ) -> Iterator[dict]:
        """Read the `raw_documents` Iterable and yield dictionaries."""
        for raw_document in raw_documents:
            try:
                yield json.loads(raw_document)
            except (TypeError, json.JSONDecodeError) as error:
                if ignore_errors:
                    logger.warning(
                        "Raised error: %s, for document %s", error, raw_document
                    )
                    continue
                logger.error("Raised error: %s, for document %s", error, raw_document)
                raise error

    @staticmethod
    def _read_json(document: Dict[str, Any]) -> Dict[str, Any]:
        """Read the `documents` row and yield for the event JSON."""
        if "event" in document:
            document["event"] = json.loads(document["event"])

        return document

    def _read_raw(self, document: Dict[str, Any]) -> bytes:
        """Read the `documents` Iterable and yield bytes."""
        # We want to return a JSON structure of the whole row, so if the event string
        # is in there we first need to serialize it so that we can deserialize the
        # whole thing.
        document = self._read_json(document)

        return json.dumps(document).encode(self.locale_encoding)
