"""Tests for Ralph clickhouse data backend."""

import json
import logging
import uuid
from datetime import datetime, timedelta

import pytest
from clickhouse_connect.driver.exceptions import ClickHouseError
from clickhouse_connect.driver.httpclient import HttpClient

from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.clickhouse import (
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


def test_backends_data_clickhouse_data_backend_default_instantiation(monkeypatch, fs):
    # pylint: disable=invalid-name
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
    assert ClickHouseDataBackend.query_model == ClickHouseQuery
    assert ClickHouseDataBackend.default_operation_type == BaseOperationType.CREATE
    assert ClickHouseDataBackend.settings_class == ClickHouseDataBackendSettings
    backend = ClickHouseDataBackend()
    assert backend.event_table_name == "xapi_events_all"
    assert backend.default_chunk_size == 500
    assert backend.locale_encoding == "utf8"


def test_backends_data_clickhouse_data_backend_instantiation_with_settings():
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
            "allow_experimental_object_type": 0,
        },
        DEFAULT_CHUNK_SIZE=1000,
        LOCALE_ENCODING="utf-16",
    )
    backend = ClickHouseDataBackend(settings)

    assert isinstance(backend.client, HttpClient)
    assert backend.event_table_name == CLICKHOUSE_TEST_TABLE_NAME
    assert backend.default_chunk_size == 1000
    assert backend.locale_encoding == "utf-16"


def test_backends_data_clickhouse_data_backend_status(
    clickhouse, clickhouse_backend, monkeypatch
):
    """Test the `ClickHouseDataBackend.status` method."""
    # pylint: disable=unused-argument

    backend = clickhouse_backend()

    assert backend.status() == DataBackendStatus.OK

    def mock_query(*_, **__):
        """Mock the ClickHouseClient.query method."""
        raise ClickHouseError("Something is wrong")

    monkeypatch.setattr(backend.client, "query", mock_query)
    assert backend.status() == DataBackendStatus.AWAY


def test_backends_data_clickhouse_data_backend_read_method_with_raw_output(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.read` method."""
    # pylint: disable=unused-argument, protected-access
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


# pylint: disable=unused-argument
def test_backends_data_clickhouse_data_backend_read_method_with_a_custom_query(
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
    documents = list(
        backend._to_insert_tuples(statements)  # pylint: disable=protected-access
    )

    backend.write(statements)

    # Test filtering
    query = ClickHouseQuery(where="event.bool = 1")
    results = list(backend.read(query=query, chunk_size=None))
    assert len(results) == 2
    assert results[0]["event"] == statements[0]
    assert results[1]["event"] == statements[2]

    # Test select fields
    query = ClickHouseQuery(select=["event_id", "event.bool"])
    results = list(backend.read(query=query))
    assert len(results) == 3
    assert len(results[0]) == 2
    assert results[0]["event_id"] == documents[0][0]
    assert results[0]["event.bool"] == statements[0]["bool"]
    assert results[1]["event_id"] == documents[1][0]
    assert results[1]["event.bool"] == statements[1]["bool"]
    assert results[2]["event_id"] == documents[2][0]
    assert results[2]["event.bool"] == statements[2]["bool"]

    # Test both
    query = ClickHouseQuery(where="event.bool = 0", select=["event_id", "event.bool"])
    results = list(backend.read(query=query))
    assert len(results) == 1
    assert len(results[0]) == 2
    assert results[0]["event_id"] == documents[1][0]
    assert results[0]["event.bool"] == statements[1]["bool"]

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
        where="event.bool = {event_bool:Bool}",
        parameters={"event_bool": 0, "format": "exact"},
    )
    results = list(backend.read(query=query))
    assert len(results) == 1
    assert results[0]["event"] == statements[1]


def test_backends_data_clickhouse_data_backend_read_method_with_failures(
    monkeypatch, caplog, clickhouse, clickhouse_backend
):  # pylint: disable=unused-argument
    """Test the `ClickHouseDataBackend.read` method with failures."""
    backend = clickhouse_backend()

    statement = {"id": str(uuid.uuid4()), "timestamp": str(datetime.utcnow())}
    document = {"event": statement}
    backend.write([statement])

    # JSON encoding error
    def mock_read_raw(*args, **kwargs):
        """Mock the `ClickHouseDataBackend._read_raw` method."""
        raise TypeError("Error")

    monkeypatch.setattr(backend, "_read_raw", mock_read_raw)

    msg = f"Failed to encode document {document}: Error"

    # Not ignoring errors
    with caplog.at_level(logging.ERROR):
        with pytest.raises(
            BackendException,
            match=msg,
        ):
            list(backend.read(raw_output=True, ignore_errors=False))

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples

    caplog.clear()

    # Ignoring errors
    with caplog.at_level(logging.WARNING):
        list(backend.read(raw_output=True, ignore_errors=True))

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
        with pytest.raises(
            BackendException,
            match=msg,
        ):
            list(backend.read(ignore_errors=True))

    assert (
        "ralph.backends.data.clickhouse",
        logging.ERROR,
        msg,
    ) in caplog.record_tuples


def test_backends_data_clickhouse_data_backend_list_method(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.list` method."""

    backend = clickhouse_backend()

    assert list(backend.list(details=True)) == [{"name": CLICKHOUSE_TEST_TABLE_NAME}]
    assert list(backend.list(details=False)) == [CLICKHOUSE_TEST_TABLE_NAME]


def test_backends_data_clickhouse_data_backend_list_method_with_failure(
    monkeypatch, caplog, clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.list` method with a failure."""
    # pylint: disable=unused-argument
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


def test_backends_data_clickhouse_data_backend_write_method_with_invalid_timestamp(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method with an invalid timestamp."""
    # pylint: disable=unused-argument
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


def test_backends_data_clickhouse_data_backend_write_method_no_timestamp(
    caplog, clickhouse_backend
):
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


def test_backends_data_clickhouse_data_backend_write_method_with_duplicated_key(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method with duplicated key
    conflict.
    """
    # pylint: disable=unused-argument
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


def test_backends_data_clickhouse_data_backend_write_method_chunks_on_error(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method imports partial chunks
    while raising BulkWriteError and ignoring errors.
    """
    # pylint: disable=unused-argument
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


def test_backends_data_clickhouse_data_backend_write_method(
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
    count = backend.write(statements, target=CLICKHOUSE_TEST_TABLE_NAME)

    assert count == 2

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 2

    sql = f"""SELECT * FROM {CLICKHOUSE_TEST_TABLE_NAME} ORDER BY event.timestamp"""
    result = list(clickhouse.query(sql).named_results())

    assert result[0]["event_id"] == native_statements[0]["id"]
    assert result[0]["emission_time"] == native_statements[0]["timestamp"]
    assert result[0]["event"] == statements[0]

    assert result[1]["event_id"] == native_statements[1]["id"]
    assert result[1]["emission_time"] == native_statements[1]["timestamp"]
    assert result[1]["event"] == statements[1]


def test_backends_data_clickhouse_data_backend_write_method_bytes(
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
    byte_data = []
    for item in statements:
        json_str = json.dumps(item, separators=(",", ":"), ensure_ascii=False)
        byte_data.append(json_str.encode("utf-8"))
    count = backend.write(byte_data, target=CLICKHOUSE_TEST_TABLE_NAME)

    assert count == 2

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 2

    sql = f"""SELECT * FROM {CLICKHOUSE_TEST_TABLE_NAME} ORDER BY event.timestamp"""
    result = list(clickhouse.query(sql).named_results())

    assert result[0]["event_id"] == native_statements[0]["id"]
    assert result[0]["emission_time"] == native_statements[0]["timestamp"]
    assert result[0]["event"] == statements[0]

    assert result[1]["event_id"] == native_statements[1]["id"]
    assert result[1]["emission_time"] == native_statements[1]["timestamp"]
    assert result[1]["event"] == statements[1]


def test_backends_data_clickhouse_data_backend_write_method_bytes_failed(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    backend = clickhouse_backend()

    byte_data = []
    json_str = "failed_json_str"
    byte_data.append(json_str.encode("utf-8"))

    count = 0
    with pytest.raises(json.JSONDecodeError):
        count = backend.write(byte_data)

    assert count == 0

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    count = backend.write(byte_data, ignore_errors=True)
    assert count == 0

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0


def test_backends_data_clickhouse_data_backend_write_method_empty(
    clickhouse, clickhouse_backend
):
    """Test the `ClickHouseDataBackend.write` method."""

    sql = f"""SELECT count(*) FROM {CLICKHOUSE_TEST_TABLE_NAME}"""
    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0

    backend = clickhouse_backend()
    count = backend.write([], target=CLICKHOUSE_TEST_TABLE_NAME)

    assert count == 0

    result = clickhouse.query(sql).result_set
    assert result[0][0] == 0


def test_backends_data_clickhouse_data_backend_write_method_wrong_operation_type(
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
    with pytest.raises(
        BackendParameterException,
        match=f"{BaseOperationType.APPEND.name} operation_type is not allowed.",
    ):
        backend.write(data=statements, operation_type=BaseOperationType.APPEND)


def test_backends_data_clickhouse_data_backend_write_method_with_custom_chunk_size(
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

    sql = f"""SELECT * FROM {CLICKHOUSE_TEST_TABLE_NAME} ORDER BY event.timestamp"""
    result = list(clickhouse.query(sql).named_results())

    assert result[0]["event_id"] == native_statements[0]["id"]
    assert result[0]["emission_time"] == native_statements[0]["timestamp"]
    assert result[0]["event"] == statements[0]

    assert result[1]["event_id"] == native_statements[1]["id"]
    assert result[1]["emission_time"] == native_statements[1]["timestamp"]
    assert result[1]["event"] == statements[1]
