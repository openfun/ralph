"""ClickHouse data backend for Ralph."""

import json
import logging
from datetime import datetime
from io import IOBase
from typing import Dict, Generator, Iterable, Iterator, List, NamedTuple, Union
from uuid import UUID, uuid4

import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError
from pydantic import BaseModel, Json, ValidationError, conint

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
)
from ralph.conf import BaseSettingsConfig, ClientOptions
from ralph.exceptions import BackendException
from ralph.utils import iter_by_batch, parse_bytes_to_dict, parse_dict_to_bytes

logger = logging.getLogger(__name__)


class ClickHouseInsert(BaseModel):
    """Model to validate required fields for ClickHouse insertion."""

    event_id: UUID
    emission_time: datetime


class ClickHouseClientOptions(ClientOptions):
    """Pydantic model for `clickhouse` client options."""

    date_time_input_format: str = "best_effort"
    allow_experimental_object_type: conint(ge=0, le=1) = 1


class InsertTuple(NamedTuple):
    """Named tuple for ClickHouse insertion."""

    event_id: UUID
    emission_time: datetime
    event: dict
    event_str: str


class ClickHouseDataBackendSettings(BaseDataBackendSettings):
    """ClickHouse data backend default configuration.

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


class BaseClickHouseQuery(BaseQuery):
    """Base ClickHouse query model."""

    select: Union[str, List[str]] = "event"
    where: Union[str, List[str], None]
    parameters: Union[Dict, None]
    limit: Union[int, None]
    sort: Union[str, None]
    column_oriented: Union[bool, None] = False


class ClickHouseQuery(BaseClickHouseQuery):
    """ClickHouse query model."""

    # pylint: disable=unsubscriptable-object
    query_string: Union[Json[BaseClickHouseQuery], None]


class ClickHouseDataBackend(BaseDataBackend):
    """ClickHouse database backend."""

    name = "clickhouse"
    query_class = ClickHouseQuery
    default_operation_type = BaseOperationType.CREATE
    unsupported_operation_types = {
        BaseOperationType.APPEND,
        BaseOperationType.DELETE,
        BaseOperationType.UPDATE,
    }
    logger = logger
    settings_class = ClickHouseDataBackendSettings
    settings: settings_class

    def __init__(self, settings: Union[settings_class, None] = None):
        """Instantiate the ClickHouse configuration.

        Args:
            settings (ClickHouseDataBackendSettings or None): The ClickHouse
                data backend settings.
        """
        super().__init__(settings)
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
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
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
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

        for table in tables:
            if details:
                yield table
            else:
                yield str(table.get("name"))

    def read(
        self,
        query: Union[str, dict, query_class, None] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Union[int, None] = None,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read documents matching the query in the target table and yield them.

        Args:
            query (str or ClickHouseQuery): The query to use when fetching documents.
            target (str or None): The target table name to query.
                If target is `None`, the `event_table_name` is used instead.
            chunk_size (int or None): The chunk size when reading documents by batches.
                If chunk_size is `None` it defaults to `default_chunk_size`.
            raw_output (bool): Controls whether to yield dictionaries or bytes.
            ignore_errors (bool): If `True`, errors during the encoding operation
                will be ignored and logged. If `False` (default), a `BackendException`
                will be raised if an error occurs.
            max_statements: The maximum number of statements to yield.

        Yield:
            bytes: The next raw document if `raw_output` is True.
            dict: The next JSON parsed document if `raw_output` is False.

        Raise:
            BackendException: If a failure occurs during ClickHouse connection.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )

    def _read_bytes(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        locale = self.settings.LOCALE_ENCODING
        statements = self._read_dicts(query, target, chunk_size, ignore_errors)
        yield from parse_dict_to_bytes(statements, locale, ignore_errors, self.logger)

    def _read_dicts(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        target = target if target else self.event_table_name
        base_query: BaseClickHouseQuery = (
            query.query_string.copy(exclude={"query_string"})
            if query.query_string
            else query.copy(exclude={"query_string"})
        )
        if isinstance(base_query.select, str):
            base_query.select = [base_query.select]

        if isinstance(base_query.where, str):
            base_query.where = [base_query.where]

        select = ",".join(base_query.select)
        sql = f"SELECT {select} FROM {target}"  # nosec

        if base_query.where:
            filter_str = "\nWHERE 1=1 AND "
            filter_str += """
            AND
            """.join(
                base_query.where
            )
            sql += filter_str

        if base_query.sort:
            sql += f"\nORDER BY {base_query.sort}"

        if base_query.limit:
            sql += f"\nLIMIT {base_query.limit}"

        self.logger.debug(
            "Start reading the %s table of the %s database (chunk size: %d)",
            target,
            self.database,
            chunk_size,
        )
        try:
            yield from self.client.query(
                sql,
                parameters=base_query.parameters,
                settings={"buffer_size": chunk_size},
                column_oriented=base_query.column_oriented,
            ).named_results()
        except (ClickHouseError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to read documents: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    def write(  # pylint: disable=too-many-arguments,useless-parent-delegation
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
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
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_bytes(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[bytes],
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        statements = parse_bytes_to_dict(data, ignore_errors, self.logger)
        return self._write_dicts(
            statements, target, chunk_size, ignore_errors, operation_type
        )

    def _write_dicts(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[dict],
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        # operation_type is either CREATE or INDEX
        target = self.event_table_name if target is None else target
        self.logger.debug(
            "Start writing to the %s table of the %s database (chunk size: %d)",
            target,
            self.database,
            chunk_size,
        )
        count = 0
        insert_tuples = self._to_insert_tuples(data, ignore_errors)
        for batch in iter_by_batch(insert_tuples, chunk_size):
            count += self._bulk_import(batch, ignore_errors, target)

        self.logger.info("Inserted a total of %d documents with success", count)
        return count

    def close(self) -> None:
        """Close the ClickHouse backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            self.logger.warning("No backend client to close.")
            return

        try:
            self.client.close()
        except ClickHouseError as error:
            msg = "Failed to close ClickHouse client: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    def _to_insert_tuples(
        self,
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
                    self.logger.warning(msg, statement)
                    continue
                self.logger.error(msg, statement)
                raise BackendException(msg % statement) from error

            insert_tuple = InsertTuple(
                insert.event_id,
                insert.emission_time,
                statement,
                json.dumps(statement),
            )

            yield insert_tuple

    def _bulk_import(
        self, batch: List[InsertTuple], ignore_errors: bool, event_table_name: str
    ):
        """Insert a batch of documents into the selected database table."""
        try:
            found_ids = {document.event_id for document in batch}

            if len(found_ids) != len(batch):
                raise BackendException("Duplicate IDs found in batch")

            self.client.insert(
                event_table_name,
                batch,
                column_names=[
                    "event_id",
                    "emission_time",
                    "event",
                    "event_str",
                ],
                # Allow ClickHouse to buffer the insert, and wait for the
                # buffer to flush. Should be configurable, but I think these are
                # reasonable defaults.
                settings={"async_insert": 1, "wait_for_async_insert": 1},
            )
        except (ClickHouseError, BackendException) as error:
            if not ignore_errors:
                raise BackendException(*error.args) from error
            msg = "Bulk import failed for current chunk but you choose to ignore it."
            self.logger.warning(msg)
            # There is no current way of knowing how many rows from the batch
            # succeeded, we assume 0 here.
            return 0

        inserted_count = len(batch)
        self.logger.debug("Inserted %d documents chunk with success", inserted_count)
        return inserted_count
