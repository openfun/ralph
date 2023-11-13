"""Tests for Ralph clickhouse data backend."""

import json
import logging
import re
import uuid
from collections import namedtuple
from datetime import datetime, timedelta

import pytest
from clickhouse_connect.driver.exceptions import ClickHouseError
from clickhouse_connect.driver.httpclient import HttpClient

from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.clickhouse import (
    ClickHouseClientOptions,
    ClickHouseDataBackend,
    ClickHouseDataBackendSettings,
    ClickHouseQuery,
)
from ralph.exceptions import BackendException, BackendParameterException

from tests.fixtures.backends import (
    CLICKHOUSE_TEST_DATABASE,
    CLICKHOUSE_TEST_HOST,
    CLICKHOUSE_TEST_PORT,
    CLICKHOUSE_TEST_TABLE_NAME,
)


def test_backends_data_clickhouse_default_instantiation(monkeypatch, fs):
    """Test the `ClickHouseDataBackend` default instantiation."""
    fs.create_file(".env")
    backend_settings_names = [
        "HOST",
        "PORT",
        "DATABASE",
        "EVENT_TABLE_NAME",
        "USERNAME",
        "PASSWORD",
        "CLIENT_OPTIONS",
        "DEFAULT_CHUNK_SIZE",
        "LOCALE_ENCODING",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__CLICKHOUSE__{name}", raising=False)

    assert ClickHouseDataBackend.name == "clickhouse"
    assert ClickHouseDataBackend.query_class == ClickHouseQuery
    assert ClickHouseDataBackend.default_operation_type == BaseOperationType.CREATE
    assert ClickHouseDataBackend.settings_class == ClickHouseDataBackendSettings
    backend = ClickHouseDataBackend()
    assert backend.settings.CLIENT_OPTIONS == ClickHouseClientOptions()
    assert backend.event_table_name == "xapi_events_all"
    assert backend.default_chunk_size == 500
    assert backend.locale_encoding == "utf8"

    # Test overriding default values with environment variables.
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATA__CLICKHOUSE__CLIENT_OPTIONS__date_time_input_format",
        "no_effort",
    )
    backend = ClickHouseDataBackend()
    assert backend.settings.CLIENT_OPTIONS == ClickHouseClientOptions(
        date_time_input_format="no_effort"
    )


def test_backends_data_clickhouse_instantiation_with_settings():
    """Test the `ClickHouseDataBackend` instantiation."""
    settings = ClickHouseDataBackendSettings(
        HOST=CLICKHOUSE_TEST_HOST,
        PORT=CLICKHOUSE_TEST_PORT,
        DATABASE=CLICKHOUSE_TEST_DATABASE,
        EVENT_TABLE_NAME=CLICKHOUSE_TEST_TABLE_NAME,
        USERNAME="default",
        PASSWORD="",
        CLIENT_OPTIONS={
            "date_time_input_format": "test_format",
        },
        DEFAULT_CHUNK_SIZE=1000,
        LOCALE_ENCODING="utf-16",
    )
    backend = ClickHouseDataBackend(settings)

    assert isinstance(backend.client, HttpClient)
    assert backend.event_table_name == CLICKHOUSE_TEST_TABLE_NAME
    assert backend.default_chunk_size == 1000
    assert backend.locale_encoding == "utf-16"
    backend.close()


def test_backends_data_clickhouse_status(clickhouse, clickhouse_backend, monkeypatch):
    """Test the `ClickHouseDataBackend.status` method."""

    backend = clickhouse_backend()

    assert backend.status() == DataBackendStatus.OK

    def mock_query(*_, **__):
        """Mock the ClickHouseClient.query method."""
        raise ClickHouseError("Something is wrong")

    monkeypatch.setattr(backend.client, "query", mock_query)
    assert backend.status() == DataBackendStatus.AWAY
    backend.close()


def test_backends_data_clickhouse_read_with_raw_output(clickhouse, clickhouse_backend):
    """Test the `ClickHouseDataBackend.read` method."""

    # Create records
    date_1 = (datetime.now() - timedelta(seconds=3)).isoformat()
    date_2 = (datetime.now() - timedelta(seconds=2)).isoformat()
    date_3 = (datetime.now() - timedelta(seconds=1)).isoformat()

    statements = [
        {"id": str(uuid.uuid4()), "bool": 1, "timestamp": date_1},
        {"id": str(uuid.uuid4()), "bool": 0, "timestamp": date_2},
        {"id": str(uuid.uuid4()), "bool": 1, "timestamp": date_3},
    ]

    backend = clickhouse_backend()
    backend.write(statements)

    results = list(backend.read())
    assert len(results) == 3
    assert results[0]["event"] == statements[0]
    assert results[1]["event"] == statements[1]
    assert results[2]["event"] == statements[2]

    results = list(backend.read(chunk_size=10))
    assert len(results) == 3
    assert results[0]["event"] == statements[0]
    assert results[1]["event"] == statements[1]
    assert results[2]["event"] == statements[2]

    results = list(backend.read(raw_output=True))
    assert len(results) == 3
    assert isinstance(results[0], bytes)
    assert json.loads(results[0])["event"] == statements[0]
    backend.close()


def test_backends_data_clickhouse_read_with_a_custom_query(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.read` method with a custom query."""
    date_1 = (datetime.now() - timedelta(seconds=3)).isoformat()
    date_2 = (datetime.now() - timedelta(seconds=2)).isoformat()
    date_3 = (datetime.now() - timedelta(seconds=1)).isoformat()

    statements = [
        {"id": str(uuid.uuid4()), "bool": 1, "timestamp": date_1},
        {"id": str(uuid.uuid4()), "bool": 0, "timestamp": date_2},
        {"id": str(uuid.uuid4()), "bool": 1, "timestamp": date_3},
    ]

    backend = clickhouse_backend()
    documents = list(backend._to_insert_tuples(statements))

    backend.write(statements)

    # Test filtering
    query = ClickHouseQuery(where="JSONExtractBool(event, 'bool') = 1")
    results = list(backend.read(query=query, chunk_size=None))
    assert len(results) == 2
    assert results[0]["event"] == statements[0]
    assert results[1]["event"] == statements[2]

    # Test select fields
    query = ClickHouseQuery(
        select=["event_id", "JSONExtractBool(event, 'bool') as bool"]
    )
    results = list(backend.read(query=query))

    assert len(results) == 3
    assert len(results[0]) == 2
    assert results[0]["event_id"] == documents[0][0]
    assert results[0]["bool"] == statements[0]["bool"]
    assert results[1]["event_id"] == documents[1][0]
    assert results[1]["bool"] == statements[1]["bool"]
    assert results[2]["event_id"] == documents[2][0]
    assert results[2]["bool"] == statements[2]["bool"]

    # Test both
    query = ClickHouseQuery(
        where="JSONExtractBool(event, 'bool') = 0",
        select=["event_id", "JSONExtractBool(event, 'bool') as bool"],
    )
    results = list(backend.read(query=query))
    assert len(results) == 1
    assert len(results[0]) == 2
    assert results[0]["event_id"] == documents[1][0]
    assert results[0]["bool"] == statements[1]["bool"]

    # Test sort
    query = ClickHouseQuery(sort="emission_time DESCENDING")
    results = list(backend.read(query=query))
    assert len(results) == 3
    assert results[0]["event"] == statements[2]
    assert results[1]["event"] == statements[1]
    assert results[2]["event"] == statements[0]

    # Test limit
    query = ClickHouseQuery(limit=1)
    results = list(backend.read(query=query))
    assert len(results) == 1
    assert results[0]["event"] == statements[0]

    # Test parameters
    query = ClickHouseQuery(
        where="JSONExtractBool(event, 'bool') = {event_bool:Bool}",
        parameters={"event_bool": 0, "format": "exact"},
    )
    results = list(backend.read(query=query))
    assert len(results) == 1
    assert results[0]["event"] == statements[1]
    backend.close()


def test_backends_data_clickhouse_read_with_failures(
    monkeypatch, caplog, clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.read` method with failures."""
    backend = clickhouse_backend()
    document = {"event": "Invalid JSON!"}

    # JSON encoding error
    def mock_clickhouse_client_query(*args, **kwargs):
        """Mock the `clickhouse.Client.query` returning an unparsable document."""
        return namedtuple("_", "named_results")(lambda: [document])

    monkeypatch.setattr(backend.client, "query", mock_clickhouse_client_query)

    msg = (
        "Failed to decode JSON: Expecting value: line 1 column 1 (char 0), "
        "for document: {'event': 'Invalid JSON!'}, at line 0"
    )

    # Not ignoring errors
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=re.escape(msg)):
            list(backend.read(raw_output=False, ignore_errors=False))

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples

    caplog.clear()

    # Ignoring errors
    with caplog.at_level(logging.WARNING):
        list(backend.read(raw_output=False, ignore_errors=True))

    assert (
        "ralph.backends.data.clickhouse",
        logging.WARNING,
        msg,
    ) in caplog.record_tuples

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        msg,
    ) not in caplog.record_tuples

    # ClickHouse error during query should raise even when ignoring errors
    def mock_query(*_, **__):
        """Mock the ClickHouseClient.query method."""
        raise ClickHouseError("Something is wrong")

    monkeypatch.setattr(backend.client, "query", mock_query)

    msg = "Failed to read documents: Something is wrong"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=re.escape(msg)):
            list(backend.read(ignore_errors=True))

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples
    backend.close()


def test_backends_data_clickhouse_list(clickhouse, clickhouse_backend):
    """Test the `ClickHouseDataBackend.list` method."""

    backend = clickhouse_backend()

    assert list(backend.list(details=True)) == [{"name": CLICKHOUSE_TEST_TABLE_NAME}]
    assert list(backend.list(details=False)) == [CLICKHOUSE_TEST_TABLE_NAME]
    backend.close()


def test_backends_data_clickhouse_list_with_failure(
    monkeypatch, caplog, clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.list` method with a failure."""

    backend = clickhouse_backend()

    def mock_query(*_, **__):
        """Mock the ClickHouseClient.query method."""
        raise ClickHouseError("Something is wrong")

    monkeypatch.setattr(backend.client, "query", mock_query)

    with caplog.at_level(logging.ERROR):
        msg = "Failed to read tables: Something is wrong"
        with pytest.raises(
            BackendException,
            match=msg,
        ):
            list(backend.list())

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples
    backend.close()


def test_backends_data_clickhouse_list_with_history(
    clickhouse_backend, caplog, monkeypatch
):
    """Test the `ClickHouseDataBackend.list` method given `new` argument set to True,
    should log a warning message.
    """
    backend = clickhouse_backend()

    def mock_clickhouse_client_query(*args, **kwargs):
        """Mock the `clickhouse.Client.query` returning no results."""
        return namedtuple("_", "named_results")(lambda: [])

    monkeypatch.setattr(backend.client, "query", mock_clickhouse_client_query)

    with caplog.at_level(logging.WARNING):
        assert not list(backend.list(new=True))

    assert (
        "ralph.backends.data.clickhouse",
        logging.WARNING,
        "The `new` argument is ignored",
    ) in caplog.record_tuples

    backend.close()


def test_backends_data_clickhouse_write_with_invalid_timestamp(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method with an invalid timestamp."""

    valid_timestamp = (datetime.now() - timedelta(seconds=3)).isoformat()
    invalid_timestamp = "This is not a valid timestamp!"
    invalid_statement = {
        "id": str(uuid.uuid4()),
        "bool": 0,
        "timestamp": invalid_timestamp,
    }

    statements = [
        {"id": str(uuid.uuid4()), "bool": 1, "timestamp": valid_timestamp},
        invalid_statement,
    ]

    backend = clickhouse_backend()

    msg = f"Statement {invalid_statement} has an invalid 'id' or 'timestamp' field"
    with pytest.raises(
        BackendException,
        match=msg,
    ):
        backend.write(statements, ignore_errors=False)
    backend.close()


def test_backends_data_clickhouse_write_no_timestamp(caplog, clickhouse_backend):
    """Test the `ClickHouseDataBackend.write` method when a statement has no
    timestamp.
    """
    statement = {"id": str(uuid.uuid4())}

    backend = clickhouse_backend()

    msg = f"Statement {statement} has an invalid 'id' or 'timestamp' field"

    # Without ignoring errors
    with caplog.at_level(logging.ERROR):
        with pytest.raises(
            BackendException,
            match=msg,
        ):
            backend.write([statement], ignore_errors=False)

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        f"Statement {statement} has an invalid 'id' or 'timestamp' field",
    ) in caplog.record_tuples

    caplog.clear()

    # Ignoring errors
    with caplog.at_level(logging.WARNING):
        backend.write([statement], ignore_errors=True)

    assert (
        "ralph.backends.data.clickhouse",
        logging.WARNING,
        f"Statement {statement} has an invalid 'id' or 'timestamp' field",
    ) in caplog.record_tuples

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        f"Statement {statement} has an invalid 'id' or 'timestamp' field",
    ) not in caplog.record_tuples
    backend.close()


def test_backends_data_clickhouse_write_with_duplicated_key(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method with duplicated key
    conflict.
    """

    backend = clickhouse_backend()

    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    dupe_id = str(uuid.uuid4())
    statements = [
        {"id": str(uuid.uuid4()), **timestamp},
        {"id": dupe_id, **timestamp},
        {"id": dupe_id, **timestamp},
    ]

    # No way of knowing how many write succeeded when there is an error
    assert backend.write(statements, ignore_errors=True) == 0

    with pytest.raises(BackendException, match="Duplicate IDs found in batch"):
        backend.write(statements, ignore_errors=False)
    backend.close()


def test_backends_data_clickhouse_write_chunks_on_error(clickhouse, clickhouse_backend):
    """Test the `ClickHouseDataBackend.write` method imports partial chunks
    while raising BulkWriteError and ignoring errors.
    """

    backend = clickhouse_backend()

    # Identical statement ID produces the same ObjectId, leading to a
    # duplicated key write error while trying to bulk import this batch
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    dupe_id = str(uuid.uuid4())
    statements = [
        {"id": str(uuid.uuid4()), **timestamp},
        {"id": dupe_id, **timestamp},
        {"id": str(uuid.uuid4()), **timestamp},
        {"id": str(uuid.uuid4()), **timestamp},
        {"id": dupe_id, **timestamp},
    ]
    assert backend.write(statements, ignore_errors=True) == 0
    backend.close()


def test_backends_data_clickhouse_write(clickhouse, clickhouse_backend):
    """Test the `ClickHouseDataBackend.write` method."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    native_statements = [
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow() - timedelta(seconds=1)},
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow()},
    ]
    statements = [
        {"id": str(x["id"]), "timestamp": x["timestamp"].isoformat()}
        for x in native_statements
    ]
    backend = clickhouse_backend()
    count = backend.write(statements, target=CLICKHOUSE_TEST_TABLE_NAME)

    assert count == 2

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 2

    sql = f"""
        SELECT *
        FROM {CLICKHOUSE_TEST_TABLE_NAME}
        ORDER BY JSONExtractString(event, 'timestamp')
    """
    result = list(clickhouse.query(sql).named_results())

    assert result[0]["event_id"] == native_statements[0]["id"]
    assert result[0]["emission_time"] == native_statements[0]["timestamp"]
    assert json.loads(result[0]["event"]) == statements[0]

    assert result[1]["event_id"] == native_statements[1]["id"]
    assert result[1]["emission_time"] == native_statements[1]["timestamp"]
    assert json.loads(result[1]["event"]) == statements[1]
    backend.close()


def test_backends_data_clickhouse_write_bytes(clickhouse, clickhouse_backend):
    """Test the `ClickHouseDataBackend.write` method."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    native_statements = [
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow() - timedelta(seconds=1)},
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow()},
    ]
    statements = [
        {"id": str(x["id"]), "timestamp": x["timestamp"].isoformat()}
        for x in native_statements
    ]

    backend = clickhouse_backend()
    byte_data = []
    for item in statements:
        json_str = json.dumps(item, separators=(",", ":"), ensure_ascii=False)
        byte_data.append(json_str.encode("utf-8"))
    count = backend.write(byte_data, target=CLICKHOUSE_TEST_TABLE_NAME)

    assert count == 2

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 2

    sql = f"""
        SELECT *
        FROM {CLICKHOUSE_TEST_TABLE_NAME}
        ORDER BY JSONExtractString(event, 'timestamp')
    """
    result = list(clickhouse.query(sql).named_results())

    assert result[0]["event_id"] == native_statements[0]["id"]
    assert result[0]["emission_time"] == native_statements[0]["timestamp"]
    assert json.loads(result[0]["event"]) == statements[0]

    assert result[1]["event_id"] == native_statements[1]["id"]
    assert result[1]["emission_time"] == native_statements[1]["timestamp"]
    assert json.loads(result[1]["event"]) == statements[1]
    backend.close()


def test_backends_data_clickhouse_write_bytes_failed(clickhouse, clickhouse_backend):
    """Test the `ClickHouseDataBackend.write` method."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    backend = clickhouse_backend()

    byte_data = []
    json_str = "failed_json_str"
    byte_data.append(json_str.encode("utf-8"))

    count = 0
    msg = (
        r"Failed to decode JSON: Expecting value: line 1 column 1 \(char 0\), "
        r"for document: b'failed_json_str', at line 0"
    )
    with pytest.raises(BackendException, match=msg):
        count = backend.write(byte_data)

    assert count == 0

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    count = backend.write(byte_data, ignore_errors=True)
    assert count == 0

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0
    backend.close()


def test_backends_data_clickhouse_write_empty(clickhouse, clickhouse_backend):
    """Test the `ClickHouseDataBackend.write` method."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    backend = clickhouse_backend()
    count = backend.write([], target=CLICKHOUSE_TEST_TABLE_NAME)

    assert count == 0

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0
    backend.close()


def test_backends_data_clickhouse_write_wrong_operation_type(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    native_statements = [
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow() - timedelta(seconds=1)},
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow()},
    ]
    statements = [
        {"id": str(x["id"]), "timestamp": x["timestamp"].isoformat()}
        for x in native_statements
    ]

    backend = clickhouse_backend()
    msg = "Append operation_type is not allowed."
    with pytest.raises(BackendParameterException, match=msg):
        backend.write(data=statements, operation_type=BaseOperationType.APPEND)
    backend.close()


def test_backends_data_clickhouse_write_with_custom_chunk_size(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method with a custom chunk_size."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    native_statements = [
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow() - timedelta(seconds=1)},
        {"id": uuid.uuid4(), "timestamp": datetime.utcnow()},
    ]
    statements = [
        {"id": str(x["id"]), "timestamp": x["timestamp"].isoformat()}
        for x in native_statements
    ]

    backend = clickhouse_backend()
    count = backend.write(statements, chunk_size=1)
    assert count == 2

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 2

    sql = f"""
        SELECT *
        FROM {CLICKHOUSE_TEST_TABLE_NAME}
        ORDER BY JSONExtractString(event, 'timestamp')
    """
    result = list(clickhouse.query(sql).named_results())

    assert result[0]["event_id"] == native_statements[0]["id"]
    assert result[0]["emission_time"] == native_statements[0]["timestamp"]
    assert json.loads(result[0]["event"]) == statements[0]

    assert result[1]["event_id"] == native_statements[1]["id"]
    assert result[1]["emission_time"] == native_statements[1]["timestamp"]
    assert json.loads(result[1]["event"]) == statements[1]
    backend.close()


def test_backends_data_clickhouse_close_with_failure(clickhouse_backend, monkeypatch):
    """Test the `ClickHouseDataBackend.close` method with failure."""

    backend = clickhouse_backend()

    def mock_connection_error():
        """ClickHouse client close mock that raises a connection error."""
        raise ClickHouseError("", (Exception("Mocked connection error"),))

    monkeypatch.setattr(backend.client, "close", mock_connection_error)

    with pytest.raises(BackendException, match="Failed to close ClickHouse client"):
        backend.close()


def test_backends_data_clickhouse_close(clickhouse_backend, caplog):
    """Test the `ClickHouseDataBackend.close` method."""

    backend = clickhouse_backend()

    # Not possible to connect to client after closing it
    backend.close()
    assert backend.status() == DataBackendStatus.AWAY

    # No client instantiated
    backend = clickhouse_backend()
    backend._client = None
    with caplog.at_level(logging.WARNING):
        backend.close()

    assert (
        "ralph.backends.data.clickhouse",
        logging.WARNING,
        "No backend client to close.",
    ) in caplog.record_tuples
