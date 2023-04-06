"""ClickHouse database backend for Ralph."""
import datetime
import json
import logging
import uuid
from dataclasses import asdict
from typing import Generator, List, Optional, TextIO, Union

import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError
from pydantic import BaseModel, ValidationError

from ralph.conf import settings
from ralph.exceptions import BackendException, BadFormatException

from .base import (
    BaseDatabase,
    BaseQuery,
    DatabaseStatus,
    StatementParameters,
    StatementQueryResult,
    enforce_query_checks,
)

clickhouse_settings = settings.BACKENDS.DATABASE.CLICKHOUSE
logger = logging.getLogger(__name__)


class ClickHouseInsert(BaseModel):
    """Model to validate required fields for ClickHouse insertion."""

    event_id: uuid.UUID
    emission_time: datetime.datetime


class ClickHouseQuery(BaseQuery):
    """ClickHouse query model."""

    where_clause: Optional[str]
    return_fields: Optional[List[str]]


class ClickHouseDatabase(BaseDatabase):
    """ClickHouse database backend."""

    name = "clickhouse"
    query_model = ClickHouseQuery

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str = clickhouse_settings.HOST,
        port: int = clickhouse_settings.PORT,
        database: str = clickhouse_settings.DATABASE,
        event_table_name: str = clickhouse_settings.EVENT_TABLE_NAME,
        username: str = clickhouse_settings.USERNAME,
        password: str = clickhouse_settings.PASSWORD,
        client_options: dict = clickhouse_settings.CLIENT_OPTIONS,
    ):
        """Instantiates the ClickHouse client.

        Args:
            host (str): ClickHouse server host to connect to.
            port (int): ClickHouse server port to connect to.
            database (str): ClickHouse database to connect to.
            event_table_name (str): Table where events live.
            username (str): ClickHouse username to connect as (optional).
            password (str): Password for the given ClickHouse username (optional).
            client_options (dict): A dictionary of valid options for the ClickHouse
                client connection.

        If username and password are None, we will try to connect as the ClickHouse
        user "default".
        """
        if client_options is None:
            client_options = {
                "date_time_input_format": "best_effort",  # Allows RFC dates
                "allow_experimental_object_type": 1,  # Allows JSON data type
            }

        self.host = host
        self.port = port
        self.database = database
        self.event_table_name = event_table_name
        self.username = username
        self.password = password

        self.client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            password=self.password,
            settings=client_options,
        )

    def status(self) -> DatabaseStatus:
        """Checks ClickHouse connection status."""
        try:
            self.client.query("SELECT 1")
        except ClickHouseError:
            return DatabaseStatus.AWAY

        return DatabaseStatus.OK

    @enforce_query_checks
    def get(self, query: ClickHouseQuery = None, chunk_size: int = 500):
        """Gets table rows and yields them."""
        fields = ",".join(query.return_fields) if query.return_fields else "event"

        sql = f"SELECT {fields} FROM {self.event_table_name}"  # nosec

        if query.where_clause:
            sql += f"  WHERE {query.where_clause}"

        result = self.client.query(sql).named_results()

        for statement in result:
            yield statement

    @staticmethod
    def to_documents(
        stream: Union[TextIO, List], ignore_errors: bool = False
    ) -> Generator[dict, None, None]:
        """Converts `stream` lines (one statement per line) to insert tuples."""
        for line in stream:
            statement = json.loads(line) if isinstance(line, str) else line

            try:
                insert = ClickHouseInsert(
                    event_id=statement["id"], emission_time=statement["timestamp"]
                )
            except (KeyError, ValidationError) as exc:
                err = (
                    "Statement has an invalid or missing id or "
                    f"timestamp field: {statement}"
                )
                if ignore_errors:
                    logger.warning(err)
                    continue
                raise BadFormatException(err) from exc

            document = (
                insert.event_id,
                insert.emission_time,
                statement,
                json.dumps(statement),
            )

            yield document

    def bulk_import(self, batch: List, ignore_errors: bool = False) -> int:
        """Inserts a batch of documents into the selected database table."""
        try:
            # ClickHouse does not do unique keys. This is a "best effort" to
            # at least check for duplicates in each batch. Overall ID checking
            # against the database happens upstream in the POST / PUT methods.
            #
            # As opposed to Mongo, the entire batch is guaranteed to fail here
            # if any dupes are found.
            found_ids = {x[0] for x in batch}

            if len(found_ids) != len(batch):
                raise BackendException("Duplicate IDs found in batch")

            self.client.insert(
                self.event_table_name,
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
            logger.warning(
                "Bulk import failed for current chunk but you choose to ignore it.",
            )
            # There is no current way of knowing how many rows from the batch
            # succeeded, we assume 0 here.
            return 0

        logger.debug("Inserted %s documents chunk with success", len(batch))

        return len(batch)

    def put(
        self,
        stream: Union[TextIO, List],
        chunk_size: int = 500,
        ignore_errors: bool = False,
    ) -> int:
        """Writes documents from the `stream` to the instance table."""
        logger.debug(
            "Start writing to the %s table of the %s database (chunk size: %d)",
            self.event_table_name,
            self.database,
            chunk_size,
        )

        rows_inserted = 0
        batch = []
        for document in self.to_documents(stream, ignore_errors=ignore_errors):
            batch.append(document)
            if len(batch) < chunk_size:
                continue

            rows_inserted += self.bulk_import(batch, ignore_errors=ignore_errors)
            batch = []

        # Catch any remaining documents when the last batch is smaller than chunk_size
        if len(batch) > 0:
            rows_inserted += self.bulk_import(batch, ignore_errors=ignore_errors)

        logger.debug("Inserted a total of %s documents with success", rows_inserted)

        return rows_inserted

    def query_statements_by_ids(self, ids: List[str]) -> List:
        """Returns the list of matching statement IDs from the database."""

        def chunk_id_list(chunk_size=10000):
            for i in range(0, len(ids), chunk_size):
                yield ids[i : i + chunk_size]

        sql = """
                SELECT event_id
                FROM {table_name:Identifier}
                WHERE event_id IN ({ids:Array(String)})
        """

        query_context = self.client.create_query_context(
            query=sql,
            parameters={"ids": ["1"], "table_name": self.event_table_name},
            column_oriented=True,
        )

        found_ids = []

        try:
            for chunk_ids in chunk_id_list():
                query_context.set_parameter("ids", chunk_ids)
                result = self.client.query(context=query_context).named_results()
                found_ids.extend(result)

            return found_ids
        except (ClickHouseError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute ClickHouse query"
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error

    def query_statements(self, params: StatementParameters) -> StatementQueryResult:
        """Returns the results of a statements query using xAPI parameters."""
        params = asdict(params)
        where_clauses = []

        if params["statementId"]:
            where_clauses.append("event_id = {statementId:UUID}")

        if params["agent"]:
            where_clauses.append("event.actor.account.name = {agent:String}")

        if params["verb"]:
            where_clauses.append("event.verb.id = {verb:String}")

        if params["activity"]:
            where_clauses.append("event.object.objectType = 'Activity'")
            where_clauses.append("event.object.id = {activity:String}")

        if params["since"]:
            where_clauses.append("emission_time > {since:DateTime64(6)}")

        if params["until"]:
            where_clauses.append("emission_time <= {until:DateTime64(6)}")

        if params["search_after"]:
            search_order = ">" if params["ascending"] else "<"

            where_clauses.append(
                f"(emission_time {search_order} "
                "{search_after:DateTime64(6)}"
                " OR "
                "(emission_time = {search_after:DateTime64(6)}"
                " AND "
                f"event_id {search_order} "
                "{pit_id:UUID}"
                "))"
            )

        sort_order = "ASCENDING" if params["ascending"] else "DESCENDING"
        order_by = f"emission_time {sort_order}, event_id {sort_order}"

        response = self._find(
            where=where_clauses, parameters=params, limit=params["limit"], sort=order_by
        )
        response = list(response)

        new_search_after = None
        new_pit_id = None

        if response:
            # Our search after string is a combination of event timestamp and
            # event id, so that we can avoid losing events when they have the
            # same timestamp, and also avoid sending the same event twice.
            new_search_after = response[-1]["emission_time"].isoformat()
            new_pit_id = str(response[-1]["event_id"])

        return StatementQueryResult(
            statements=[document["event"] for document in response],
            search_after=new_search_after,
            pit_id=new_pit_id,
        )

    def _find(
        self, parameters: dict, where: List = None, limit: int = None, sort: str = None
    ):
        """Wraps the ClickHouse query method.

        Raises:
            BackendException: raised for any failure.
        """
        sql = """
        SELECT event_id, emission_time, event
        FROM {event_table_name:Identifier}
        """
        if where:
            filter_str = "WHERE 1=1 AND "
            filter_str += """
            AND
            """.join(
                where
            )
            sql += filter_str
        if sort:
            sql += f"\nORDER BY {sort}"

        if limit:
            sql += f"\nLIMIT {limit}"

        parameters["event_table_name"] = self.event_table_name

        try:
            return self.client.query(sql, parameters=parameters).named_results()
        except (ClickHouseError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute ClickHouse query"
            logger.error("%s. %s", msg, error)
            raise BackendException(msg, *error.args) from error
