"""Tests for Ralph Elasticsearch data backend."""

import json
import logging
import random
import re
from collections.abc import Iterable
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pytest
from elastic_transport import ApiResponseMeta
from elasticsearch import ApiError, Elasticsearch
from elasticsearch import ConnectionError as ESConnectionError

from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.es import (
    ESClientOptions,
    ESDataBackend,
    ESDataBackendSettings,
    ESQuery,
)
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now

from tests.fixtures.backends import (
    ES_TEST_FORWARDING_INDEX,
    ES_TEST_INDEX,
    get_es_fixture,
)


def test_backends_data_es_data_backend_default_instantiation(monkeypatch, fs):
    """Test the `ESDataBackend` default instantiation."""

    fs.create_file(".env")
    backend_settings_names = [
        "ALLOW_YELLOW_STATUS",
        "CLIENT_OPTIONS",
        "CLIENT_OPTIONS__ca_certs",
        "CLIENT_OPTIONS__verify_certs",
        "DEFAULT_CHUNK_SIZE",
        "DEFAULT_INDEX",
        "HOSTS",
        "LOCALE_ENCODING",
        "POINT_IN_TIME_KEEP_ALIVE",
        "REFRESH_AFTER_WRITE",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__ES__{name}", raising=False)

    assert ESDataBackend.name == "es"
    assert ESDataBackend.query_class == ESQuery
    assert ESDataBackend.default_operation_type == BaseOperationType.INDEX
    assert ESDataBackend.settings_class == ESDataBackendSettings
    backend = ESDataBackend()
    assert not backend.settings.ALLOW_YELLOW_STATUS
    assert backend.settings.CLIENT_OPTIONS == ESClientOptions()
    assert backend.settings.DEFAULT_CHUNK_SIZE == 500
    assert backend.settings.DEFAULT_INDEX == "statements"
    assert backend.settings.HOSTS == ("http://localhost:9200",)
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.POINT_IN_TIME_KEEP_ALIVE == "1m"
    assert not backend.settings.REFRESH_AFTER_WRITE
    assert isinstance(backend.client, Elasticsearch)
    elasticsearch_node = backend.client.transport.node_pool.get()
    assert elasticsearch_node.config.ca_certs is None
    assert elasticsearch_node.config.verify_certs is None
    assert elasticsearch_node.host == "localhost"
    assert elasticsearch_node.port == 9200

    # Test overriding default values with environment variables.
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATA__ES__CLIENT_OPTIONS__verify_certs",
        True,
    )
    backend = ESDataBackend()
    assert backend.settings.CLIENT_OPTIONS == ESClientOptions(verify_certs=True)


def test_backends_data_es_data_backend_instantiation_with_settings():
    """Test the `ESDataBackend` instantiation with settings."""
    settings = ESDataBackendSettings(
        ALLOW_YELLOW_STATUS=True,
        CLIENT_OPTIONS={"verify_certs": True, "ca_certs": "/path/to/ca/bundle"},
        DEFAULT_CHUNK_SIZE=5000,
        DEFAULT_INDEX=ES_TEST_INDEX,
        HOSTS=["https://elasticsearch_hostname:9200"],
        LOCALE_ENCODING="utf-16",
        POINT_IN_TIME_KEEP_ALIVE="5m",
        REFRESH_AFTER_WRITE=True,
    )
    backend = ESDataBackend(settings)
    assert backend.settings.ALLOW_YELLOW_STATUS
    assert backend.settings.CLIENT_OPTIONS == ESClientOptions(
        verify_certs=True, ca_certs="/path/to/ca/bundle"
    )
    assert backend.settings.DEFAULT_CHUNK_SIZE == 5000
    assert backend.settings.DEFAULT_INDEX == ES_TEST_INDEX
    assert backend.settings.HOSTS == ("https://elasticsearch_hostname:9200",)
    assert backend.settings.LOCALE_ENCODING == "utf-16"
    assert backend.settings.POINT_IN_TIME_KEEP_ALIVE == "5m"
    assert backend.settings.REFRESH_AFTER_WRITE
    assert isinstance(backend.client, Elasticsearch)
    elasticsearch_node = backend.client.transport.node_pool.get()
    assert elasticsearch_node.config.ca_certs == Path("/path/to/ca/bundle")
    assert elasticsearch_node.config.verify_certs is True
    assert elasticsearch_node.host == "elasticsearch_hostname"
    assert elasticsearch_node.port == 9200
    assert backend.settings.POINT_IN_TIME_KEEP_ALIVE == "5m"

    try:
        ESDataBackend(settings)
    except Exception as err:  # noqa: BLE001
        pytest.fail(f"Two ESDataBackends should not raise exceptions: {err}")

    backend.close()


def test_backends_data_es_data_backend_status_method(monkeypatch, es_backend, caplog):
    """Test the `ESDataBackend.status` method."""
    backend = es_backend()
    with monkeypatch.context() as elasticsearch_patch:
        # Given green status, the `status` method should return `DataBackendStatus.OK`.
        es_status = "1664532320 10:05:20 docker-cluster green 1 1 2 2 0 0 1 0 - 66.7%"
        elasticsearch_patch.setattr(backend.client, "info", lambda: None)
        elasticsearch_patch.setattr(backend.client.cat, "health", lambda: es_status)
        assert backend.status() == DataBackendStatus.OK

    with monkeypatch.context() as elasticsearch_patch:
        # Given yellow status, the `status` method should return
        # `DataBackendStatus.ERROR`.
        es_status = "1664532320 10:05:20 docker-cluster yellow 1 1 2 2 0 0 1 0 - 66.7%"
        elasticsearch_patch.setattr(backend.client, "info", lambda: None)
        elasticsearch_patch.setattr(backend.client.cat, "health", lambda: es_status)
        assert backend.status() == DataBackendStatus.ERROR
        # Given yellow status, and `settings.ALLOW_YELLOW_STATUS` set to `True`,
        # the `status` method should return `DataBackendStatus.OK`.
        backend.settings.ALLOW_YELLOW_STATUS = True
        with caplog.at_level(logging.INFO):
            assert backend.status() == DataBackendStatus.OK

    assert (
        "ralph.backends.data.es",
        logging.INFO,
        "Cluster status is yellow.",
    ) in caplog.record_tuples

    # Given a connection exception, the `status` method should return
    # `DataBackendStatus.ERROR`.
    with monkeypatch.context() as elasticsearch_patch:

        def mock_connection_error():
            """ES client info mock that raises a connection error."""
            raise ESConnectionError("", (Exception("Mocked connection error"),))

        elasticsearch_patch.setattr(backend.client, "info", mock_connection_error)
        with caplog.at_level(logging.ERROR):
            assert backend.status() == DataBackendStatus.AWAY

    assert (
        "ralph.backends.data.es",
        logging.ERROR,
        "Failed to connect to Elasticsearch: Connection error caused by: "
        "Exception(Mocked connection error)",
    ) in caplog.record_tuples

    backend.close()


@pytest.mark.parametrize(
    "exception, error",
    [
        (ApiError("", ApiResponseMeta(*([None] * 5)), None), "ApiError(None, '')"),
        (ESConnectionError(""), "Connection error"),
    ],
)
def test_backends_data_es_data_backend_list_method_with_failure(
    exception, error, caplog, monkeypatch, es_backend
):
    """Test the `ESDataBackend.list` method given an failed Elasticsearch connection
    should raise a `BackendException` and log an error message.
    """

    def mock_get(index):
        """Mock the ES.client.indices.get method raising an exception."""
        assert index == "*"
        raise exception

    backend = es_backend()
    monkeypatch.setattr(backend.client.indices, "get", mock_get)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            next(backend.list())

    assert (
        "ralph.backends.data.es",
        logging.ERROR,
        f"Failed to read indices: {error}",
    ) in caplog.record_tuples

    backend.close()


def test_backends_data_es_data_backend_list_method_without_history(
    es_backend, monkeypatch
):
    """Test the `ESDataBackend.list` method without history."""

    indices = {"index_1": {"info_1": "foo"}, "index_2": {"info_2": "baz"}}

    def mock_get(index):
        """Mock the ES.client.indices.get method returning a dictionary."""
        assert index == "target_index*"
        return indices

    backend = es_backend()
    monkeypatch.setattr(backend.client.indices, "get", mock_get)
    result = backend.list("target_index*")
    assert isinstance(result, Iterable)
    assert list(result) == list(indices.keys())

    backend.close()


def test_backends_data_es_data_backend_list_method_with_details(
    es_backend, monkeypatch
):
    """Test the `ESDataBackend.list` method with `details` set to `True`."""
    indices = {"index_1": {"info_1": "foo"}, "index_2": {"info_2": "baz"}}

    def mock_get(index):
        """Mock the ES.client.indices.get method returning a dictionary."""
        assert index == "target_index*"
        return indices

    backend = es_backend()
    monkeypatch.setattr(backend.client.indices, "get", mock_get)
    result = backend.list("target_index*", details=True)
    assert isinstance(result, Iterable)
    assert list(result) == [
        {"index_1": {"info_1": "foo"}},
        {"index_2": {"info_2": "baz"}},
    ]

    backend.close()


def test_backends_data_es_data_backend_list_method_with_history(
    es_backend, caplog, monkeypatch
):
    """Test the `ESDataBackend.list` method given `new` argument set to True, should log
    a warning message.
    """
    backend = es_backend()
    monkeypatch.setattr(backend.client.indices, "get", lambda index: {})
    with caplog.at_level(logging.WARNING):
        assert not list(backend.list(new=True))

    assert (
        "ralph.backends.data.es",
        logging.WARNING,
        "The `new` argument is ignored",
    ) in caplog.record_tuples

    backend.close()


@pytest.mark.parametrize(
    "exception, error",
    [
        (ApiError("", ApiResponseMeta(*([None] * 5)), None), r"ApiError\(None, ''\)"),
        (ESConnectionError(""), "Connection error"),
    ],
)
def test_backends_data_es_data_backend_read_method_with_failure(  # noqa: PLR0913
    exception, error, es, es_backend, caplog, monkeypatch
):
    """Test the `ESDataBackend.read` method, given a request failure, should raise a
    `BackendException`.
    """

    def mock_es_search_open_pit(**kwargs):
        """Mock the ES.client.search and open_point_in_time methods always raising an
        exception.
        """
        raise exception

    backend = es_backend()

    # Search failure.
    monkeypatch.setattr(backend.client, "search", mock_es_search_open_pit)
    with pytest.raises(
        BackendException, match=f"Failed to execute Elasticsearch query: {error}"
    ):
        with caplog.at_level(logging.ERROR):
            next(backend.read())

    assert (
        "ralph.backends.data.es",
        logging.ERROR,
        "Failed to execute Elasticsearch query: %s" % error.replace("\\", ""),
    ) in caplog.record_tuples

    # Open point in time failure.
    monkeypatch.setattr(backend.client, "open_point_in_time", mock_es_search_open_pit)
    with pytest.raises(
        BackendException, match=f"Failed to open Elasticsearch point in time: {error}"
    ):
        with caplog.at_level(logging.ERROR):
            next(backend.read())

    error = error.replace("\\", "")
    assert (
        "ralph.backends.data.es",
        logging.ERROR,
        "Failed to open Elasticsearch point in time: %s" % error.replace("\\", ""),
    ) in caplog.record_tuples

    backend.close()


def test_backends_data_es_data_backend_read_method_with_ignore_errors(
    es, es_backend, monkeypatch, caplog
):
    """Test the `ESDataBackend.read` method, given `ignore_errors` set to `True`,
    should log a warning message.
    """

    backend = es_backend()
    monkeypatch.setattr(backend.client, "search", lambda **_: {"hits": {"hits": []}})
    with caplog.at_level(logging.WARNING):
        list(backend.read(ignore_errors=True))

    assert (
        "ralph.backends.data.es",
        logging.WARNING,
        "The `ignore_errors` argument is ignored",
    ) in caplog.record_tuples

    backend.close()


def test_backends_data_es_data_backend_read_method_with_raw_ouput(es, es_backend):
    """Test the `ESDataBackend.read` method with `raw_output` set to `True`."""

    backend = es_backend()
    documents = [{"id": idx, "timestamp": now()} for idx in range(10)]
    assert backend.write(documents) == 10
    hits = list(backend.read(raw_output=True))
    for i, hit in enumerate(hits):
        assert isinstance(hit, bytes)
        assert json.loads(hit).get("_source") == documents[i]

    backend.close()


def test_backends_data_es_data_backend_read_method_without_raw_ouput(es, es_backend):
    """Test the `ESDataBackend.read` method with `raw_output` set to `False`."""

    backend = es_backend()
    documents = [{"id": idx, "timestamp": now()} for idx in range(10)]
    assert backend.write(documents) == 10
    hits = backend.read()
    for i, hit in enumerate(hits):
        assert isinstance(hit, dict)
        assert hit.get("_source") == documents[i]

    backend.close()


def test_backends_data_es_data_backend_read_method_with_query(es, es_backend, caplog):
    """Test the `ESDataBackend.read` method with a query."""

    backend = es_backend()
    documents = [{"id": idx, "timestamp": now(), "modulo": idx % 2} for idx in range(5)]
    assert backend.write(documents) == 5
    # Find every even item.
    query = ESQuery(query={"term": {"modulo": 0}})
    results = list(backend.read(query=query))
    assert len(results) == 3
    assert results[0]["_source"]["id"] == 0
    assert results[1]["_source"]["id"] == 2
    assert results[2]["_source"]["id"] == 4

    # Find the first two even items.
    query = ESQuery(query={"term": {"modulo": 0}}, size=2)
    results = list(backend.read(query=query))
    assert len(results) == 2
    assert results[0]["_source"]["id"] == 0
    assert results[1]["_source"]["id"] == 2

    # Find the first ten even items although there are only three available.
    query = ESQuery(query={"term": {"modulo": 0}}, size=10)
    results = list(backend.read(query=query))
    assert len(results) == 3
    assert results[0]["_source"]["id"] == 0
    assert results[1]["_source"]["id"] == 2
    assert results[2]["_source"]["id"] == 4

    # Find every odd item.
    query = {"query": {"term": {"modulo": 1}}}
    results = list(backend.read(query=query))
    assert len(results) == 2
    assert results[0]["_source"]["id"] == 1
    assert results[1]["_source"]["id"] == 3

    # Find documents with ID equal to one or five.
    query = "id:(1 OR 5)"
    results = list(backend.read(query=query))
    assert len(results) == 1
    assert results[0]["_source"]["id"] == 1

    # Check query argument type
    with pytest.raises(
        BackendParameterException,
        match="'query' argument is expected to be a ESQuery instance.",
    ):
        with caplog.at_level(logging.ERROR):
            list(backend.read(query={"not_query": "foo"}))

    assert (
        "ralph.backends.data.base",
        logging.ERROR,
        "The 'query' argument is expected to be a ESQuery instance. "
        "[{'loc': ('not_query',), 'msg': 'extra fields not permitted', "
        "'type': 'value_error.extra'}]",
    ) in caplog.record_tuples

    backend.close()


def test_backends_data_es_data_backend_write_method_with_create_operation(
    es, es_backend, caplog
):
    """Test the `ESDataBackend.write` method, given an `CREATE` `operation_type`,
    should insert the target documents with the provided data.
    """

    backend = es_backend()
    assert len(list(backend.read())) == 0

    # Given an empty data iterator, the write method should return 0 and log a message.
    data = []
    with caplog.at_level(logging.INFO):
        assert backend.write(data, operation_type=BaseOperationType.CREATE) == 0

    assert (
        "ralph.backends.data.es",
        logging.INFO,
        "Data Iterator is empty; skipping write to target.",
    ) in caplog.record_tuples

    # Given an iterator with multiple documents, the write method should write the
    # documents to the default target index.
    data = ({"value": str(idx)} for idx in range(9))
    with caplog.at_level(logging.DEBUG):
        assert (
            backend.write(data, chunk_size=5, operation_type=BaseOperationType.CREATE)
            == 9
        )

    write_records = 0
    for record in caplog.record_tuples:
        if re.match(r"^Wrote 1 document \[action: \{.*\}\]$", record[2]):
            write_records += 1
    assert write_records == 9

    assert (
        "ralph.backends.data.es",
        logging.INFO,
        "Finished writing 9 documents with success",
    ) in caplog.record_tuples

    hits = list(backend.read())
    assert [hit["_source"] for hit in hits] == [{"value": str(idx)} for idx in range(9)]

    backend.close()


def test_backends_data_es_data_backend_write_method_with_delete_operation(
    es,
    es_backend,
):
    """Test the `ESDataBackend.write` method, given a `DELETE` `operation_type`, should
    remove the target documents.
    """

    backend = es_backend()
    data = [{"id": idx, "value": str(idx)} for idx in range(10)]

    assert len(list(backend.read())) == 0
    assert backend.write(data, chunk_size=5) == 10

    data = [{"id": idx} for idx in range(3)]
    assert (
        backend.write(data, chunk_size=5, operation_type=BaseOperationType.DELETE) == 3
    )

    hits = list(backend.read())
    assert len(hits) == 7
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(3, 10))

    backend.close()


def test_backends_data_es_data_backend_write_method_with_update_operation(
    es,
    es_backend,
):
    """Test the `ESDataBackend.write` method, given an `UPDATE` `operation_type`, should
    overwrite the target documents with the provided data.
    """

    backend = es_backend()
    data = BytesIO(
        "\n".join(
            [json.dumps({"id": idx, "value": str(idx)}) for idx in range(10)]
        ).encode("utf8")
    )

    assert len(list(backend.read())) == 0
    assert backend.write(data, chunk_size=5) == 10

    hits = list(backend.read())
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))
    assert sorted([hit["_source"]["value"] for hit in hits]) == list(
        map(str, range(10))
    )

    data = BytesIO(
        "\n".join(
            [json.dumps({"id": idx, "value": str(10 + idx)}) for idx in range(10)]
        ).encode("utf8")
    )

    assert (
        backend.write(data, chunk_size=5, operation_type=BaseOperationType.UPDATE) == 10
    )

    hits = list(backend.read())
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))
    assert sorted([hit["_source"]["value"] for hit in hits]) == [
        str(x + 10) for x in range(10)
    ]

    backend.close()


def test_backends_data_es_data_backend_write_method_with_append_operation(
    es_backend, caplog
):
    """Test the `ESDataBackend.write` method, given an `APPEND` `operation_type`,
    should raise a `BackendParameterException`.
    """
    backend = es_backend()
    msg = "Append operation_type is not supported."
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            backend.write(data=[{}], operation_type=BaseOperationType.APPEND)

    assert (
        "ralph.backends.data.es",
        logging.ERROR,
        "Append operation_type is not supported.",
    ) in caplog.record_tuples

    backend.close()


def test_backends_data_es_data_backend_write_method_with_target(es, es_backend):
    """Test the `ESDataBackend.write` method, given a target index, should insert
    documents to the corresponding index.
    """

    backend = es_backend()

    def get_data():
        """Yield data."""
        yield {"value": "1"}
        yield {"value": "2"}

    # Create second Elasticsearch index.
    for _ in get_es_fixture(index=ES_TEST_FORWARDING_INDEX):
        # Both indexes should be empty.
        assert len(list(backend.read())) == 0
        assert len(list(backend.read(target=ES_TEST_FORWARDING_INDEX))) == 0

        # Write to forwarding index.
        assert backend.write(get_data(), target=ES_TEST_FORWARDING_INDEX) == 2

        hits = list(backend.read())
        hits_with_target = list(backend.read(target=ES_TEST_FORWARDING_INDEX))
        # No documents should be inserted into the default index.
        assert not hits
        # Documents should be inserted into the target index.
        assert [hit["_source"] for hit in hits_with_target] == [
            {"value": "1"},
            {"value": "2"},
        ]

    backend.close()


def test_backends_data_es_data_backend_write_method_without_ignore_errors(
    es, es_backend, caplog
):
    """Test the `ESDataBackend.write` method with `ignore_errors` set to `False`, given
    badly formatted data, should raise a `BackendException`.
    """

    data = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    data[4].update({"count": "wrong"})

    backend = es_backend()
    assert len(list(backend.read())) == 0

    # By default, we should raise an error and stop the importation.
    msg = (
        r"1 document\(s\) failed to index. "
        r"\[\{'index': \{'_index': 'test-index-foo', '_id': '4', 'status': 400, 'error'"
        r": \{'type': 'mapper_parsing_exception', 'reason': \"failed to parse field "
        r"\[count\] of type \[long\] in document with id '4'. Preview of field's value:"
        r" 'wrong'\", 'caused_by': \{'type': 'illegal_argument_exception', 'reason': "
        r"'For input string: \"wrong\"'\}\}, 'data': \{'id': 4, 'count': 'wrong'\}\}\}"
        r"\] Total succeeded writes: 5"
    )
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            backend.write(data, chunk_size=2)

    assert (
        "ralph.backends.data.es",
        logging.ERROR,
        msg.replace("\\", ""),
    ) in caplog.record_tuples

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = list(backend.read())
    assert len(hits) == 5
    assert sorted([hit["_source"]["id"] for hit in hits]) == [0, 1, 2, 3, 5]

    # Given an unparsable binary JSON document, the write method should raise a
    # `BackendException`.
    data = [
        json.dumps({"foo": "bar"}).encode("utf-8"),
        "This is invalid JSON".encode("utf-8"),
        json.dumps({"foo": "baz"}).encode("utf-8"),
    ]

    # By default, we should raise an error and stop the importation.
    msg = (
        r"Failed to decode JSON: Expecting value: line 1 column 1 \(char 0\), "
        r"for document: b'This is invalid JSON'"
    )
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            backend.write(data, chunk_size=2)

    assert (
        "ralph.backends.data.es",
        logging.ERROR,
        msg.replace("\\", ""),
    ) in caplog.record_tuples

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = list(backend.read())
    assert len(hits) == 5

    backend.close()


def test_backends_data_es_data_backend_write_method_with_ignore_errors(es, es_backend):
    """Test the `ESDataBackend.write` method with `ignore_errors` set to `True`, given
    badly formatted data, should should skip the invalid data.
    """

    records = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    records[2].update({"count": "wrong"})

    backend = es_backend()
    assert len(list(backend.read())) == 0

    assert backend.write(records, chunk_size=2, ignore_errors=True) == 9

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = list(backend.read())
    assert len(hits) == 9
    assert sorted([hit["_source"]["id"] for hit in hits]) == [
        i for i in range(10) if i != 2
    ]

    # Given an unparsable binary JSON document, the write method should skip it.
    data = [
        json.dumps({"foo": "bar"}).encode("utf-8"),
        "This is invalid JSON".encode("utf-8"),
        json.dumps({"foo": "baz"}).encode("utf-8"),
    ]
    assert backend.write(data, chunk_size=2, ignore_errors=True) == 2

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = list(backend.read())
    assert len(hits) == 11
    assert [hit["_source"] for hit in hits[9:]] == [{"foo": "bar"}, {"foo": "baz"}]

    backend.close()


def test_backends_data_es_data_backend_write_method_with_datastream(
    es_data_stream, es_backend
):
    """Test the `ESDataBackend.write` method using a configured data stream."""

    data = [{"id": idx, "@timestamp": datetime.now().isoformat()} for idx in range(10)]
    backend = es_backend()
    assert len(list(backend.read())) == 0
    assert (
        backend.write(data, chunk_size=5, operation_type=BaseOperationType.CREATE) == 10
    )

    hits = list(backend.read())
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))

    backend.close()


def test_backends_data_es_data_backend_close_method_with_failure(
    es_backend, monkeypatch
):
    """Test the `ESDataBackend.close` method."""

    backend = es_backend()

    def mock_connection_error():
        """ES client close mock that raises a connection error."""
        raise ESConnectionError("", (Exception("Mocked connection error"),))

    monkeypatch.setattr(backend.client, "close", mock_connection_error)

    with pytest.raises(BackendException, match="Failed to close Elasticsearch client"):
        backend.close()


def test_backends_data_es_data_backend_close_method(es_backend, caplog):
    """Test the `ESDataBackend.close` method."""

    backend = es_backend()
    backend.status()

    # Not possible to connect to client after closing it
    backend.close()
    assert backend.status() == DataBackendStatus.AWAY

    # No client instantiated
    backend = es_backend()
    backend._client = None
    with caplog.at_level(logging.WARNING):
        backend.close()

    assert (
        "ralph.backends.data.es",
        logging.WARNING,
        "No backend client to close.",
    ) in caplog.record_tuples
