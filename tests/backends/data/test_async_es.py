"""Tests for Ralph Async Elasticsearch data backend."""

import json
import logging
import random
import re
from collections.abc import Iterable
from datetime import datetime
from io import BytesIO

import pytest
from elastic_transport import ApiResponseMeta
from elasticsearch import ApiError, AsyncElasticsearch
from elasticsearch import ConnectionError as ESConnectionError

from ralph.backends.data.async_es import (
    AsyncESDataBackend,
    ESDataBackendSettings,
    ESQuery,
)
from ralph.backends.data.base import AsyncWritable, BaseOperationType, DataBackendStatus
from ralph.backends.data.es import ESClientOptions
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now

from tests.fixtures.backends import (
    ES_TEST_FORWARDING_INDEX,
    ES_TEST_INDEX,
    get_es_fixture,
)


@pytest.mark.anyio
async def test_backends_data_async_es_default_instantiation(monkeypatch, fs):
    """Test the `AsyncESDataBackend` default instantiation."""

    fs.create_file(".env")
    backend_settings_names = [
        "ALLOW_YELLOW_STATUS",
        "CLIENT_OPTIONS",
        "CLIENT_OPTIONS__ca_certs",
        "CLIENT_OPTIONS__verify_certs",
        "DEFAULT_INDEX",
        "HOSTS",
        "LOCALE_ENCODING",
        "READ_CHUNK_SIZE",
        "POINT_IN_TIME_KEEP_ALIVE",
        "WRITE_CHUNK_SIZE",
        "REFRESH_AFTER_WRITE",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__ES__{name}", raising=False)

    assert AsyncESDataBackend.name == "async_es"
    assert AsyncESDataBackend.query_class == ESQuery
    assert AsyncESDataBackend.default_operation_type == BaseOperationType.INDEX
    assert AsyncESDataBackend.settings_class == ESDataBackendSettings
    backend = AsyncESDataBackend()
    assert not backend.settings.ALLOW_YELLOW_STATUS
    assert backend.settings.CLIENT_OPTIONS == ESClientOptions()
    assert backend.settings.DEFAULT_INDEX == "statements"
    assert backend.settings.HOSTS == ("http://localhost:9200",)
    assert backend.settings.LOCALE_ENCODING == "utf8"
    assert backend.settings.POINT_IN_TIME_KEEP_ALIVE == "1m"
    assert backend.settings.READ_CHUNK_SIZE == 500
    assert not backend.settings.REFRESH_AFTER_WRITE
    assert backend.settings.WRITE_CHUNK_SIZE == 500
    assert isinstance(backend.client, AsyncElasticsearch)
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
    backend = AsyncESDataBackend()
    assert backend.settings.CLIENT_OPTIONS == ESClientOptions(verify_certs=True)


@pytest.mark.anyio
async def test_backends_data_async_es_instantiation_with_settings():
    """Test the `AsyncESDataBackend` instantiation with settings."""
    # Not testing `ca_certs` and `verify_certs` as elasticsearch aiohttp
    # node transport checks that file exists
    settings = ESDataBackendSettings(
        ALLOW_YELLOW_STATUS=True,
        CLIENT_OPTIONS={"verify_certs": False, "ca_certs": None},
        DEFAULT_INDEX=ES_TEST_INDEX,
        HOSTS=["https://elasticsearch_hostname:9200"],
        LOCALE_ENCODING="utf-16",
        POINT_IN_TIME_KEEP_ALIVE="5m",
        READ_CHUNK_SIZE=5000,
        REFRESH_AFTER_WRITE=True,
        WRITE_CHUNK_SIZE=4999,
    )
    backend = AsyncESDataBackend(settings)
    assert backend.settings.ALLOW_YELLOW_STATUS
    assert backend.settings.CLIENT_OPTIONS == ESClientOptions(
        verify_certs=False, ca_certs=None
    )
    assert backend.settings.DEFAULT_INDEX == ES_TEST_INDEX
    assert backend.settings.HOSTS == ("https://elasticsearch_hostname:9200",)
    assert backend.settings.LOCALE_ENCODING == "utf-16"
    assert backend.settings.POINT_IN_TIME_KEEP_ALIVE == "5m"
    assert backend.settings.READ_CHUNK_SIZE == 5000
    assert backend.settings.REFRESH_AFTER_WRITE
    assert backend.settings.WRITE_CHUNK_SIZE == 4999
    assert isinstance(backend.client, AsyncElasticsearch)
    elasticsearch_node = backend.client.transport.node_pool.get()
    assert elasticsearch_node.host == "elasticsearch_hostname"
    assert elasticsearch_node.port == 9200
    assert backend.settings.POINT_IN_TIME_KEEP_ALIVE == "5m"

    try:
        AsyncESDataBackend(settings)
    except Exception as err:  # noqa: BLE001
        pytest.fail(f"Two AsyncESDataBackends should not raise exceptions: {err}")


@pytest.mark.anyio
async def test_backends_data_async_es_status(monkeypatch, async_es_backend, caplog):
    """Test the `AsyncESDataBackend.status` method."""

    async def mock_info():
        return None

    def mock_health_status(es_status):
        async def mock_health():
            return es_status

        return mock_health

    backend = async_es_backend()

    # Given green status, the `status` method should return `DataBackendStatus.OK`.
    with monkeypatch.context() as elasticsearch_patch:
        es_status = "1664532320 10:05:20 docker-cluster green 1 1 2 2 0 0 1 0 - 66.7%"
        elasticsearch_patch.setattr(backend.client, "info", mock_info)
        elasticsearch_patch.setattr(
            backend.client.cat, "health", mock_health_status(es_status)
        )
        assert await backend.status() == DataBackendStatus.OK

    with monkeypatch.context() as elasticsearch_patch:
        # Given yellow status, the `status` method should return
        # `DataBackendStatus.ERROR`.
        es_status = "1664532320 10:05:20 docker-cluster yellow 1 1 2 2 0 0 1 0 - 66.7%"
        elasticsearch_patch.setattr(backend.client, "info", mock_info)
        elasticsearch_patch.setattr(
            backend.client.cat, "health", mock_health_status(es_status)
        )
        assert await backend.status() == DataBackendStatus.ERROR
        # Given yellow status, and `settings.ALLOW_YELLOW_STATUS` set to `True`,
        # the `status` method should return `DataBackendStatus.OK`.
        elasticsearch_patch.setattr(backend.settings, "ALLOW_YELLOW_STATUS", True)
        with caplog.at_level(logging.INFO):
            assert await backend.status() == DataBackendStatus.OK

        assert (
            "ralph.backends.data.async_es",
            logging.INFO,
            "Cluster status is yellow.",
        ) in caplog.record_tuples

    # Given a connection exception, the `status` method should return
    # `DataBackendStatus.ERROR`.
    with monkeypatch.context() as elasticsearch_patch:

        async def mock_connection_error():
            """ES client info mock that raises a connection error."""
            raise ESConnectionError("", (Exception("Mocked connection error"),))

        elasticsearch_patch.setattr(backend.client, "info", mock_connection_error)
        with caplog.at_level(logging.ERROR):
            assert await backend.status() == DataBackendStatus.AWAY

    assert (
        "ralph.backends.data.async_es",
        logging.ERROR,
        "Failed to connect to Elasticsearch: Connection error caused by: "
        "Exception(Mocked connection error)",
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.parametrize(
    "exception, error",
    [
        (ApiError("", ApiResponseMeta(*([None] * 5)), None), "ApiError(None, '')"),
        (ESConnectionError(""), "Connection error"),
    ],
)
@pytest.mark.anyio
async def test_backends_data_async_es_list_with_failure(
    exception, error, caplog, monkeypatch, async_es_backend
):
    """Test the `AsyncESDataBackend.list` method given a failed Elasticsearch connection
    should raise a `BackendException` and log an error message.
    """

    async def mock_get(index):
        """Mocks the AsyncES.client.indices.get method always raising an exception."""
        assert index == "*"
        raise exception

    backend = async_es_backend()
    monkeypatch.setattr(backend.client.indices, "get", mock_get)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            async for result in backend.list():
                next(result)

    assert (
        "ralph.backends.data.async_es",
        logging.ERROR,
        f"Failed to read indices: {error}",
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_list_without_history(
    async_es_backend, monkeypatch
):
    """Test the `AsyncESDataBackend.list` method without history."""

    indices = {"index_1": {"info_1": "foo"}, "index_2": {"info_2": "baz"}}

    async def mock_get(index):
        """Mocks the AsyncES.client.indices.get method returning a dictionary."""
        assert index == "target_index*"
        return indices

    backend = async_es_backend()
    monkeypatch.setattr(backend.client.indices, "get", mock_get)
    result = [statement async for statement in backend.list("target_index*")]
    assert isinstance(result, Iterable)
    assert list(result) == list(indices.keys())

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_list_with_history(
    async_es_backend, caplog, monkeypatch
):
    """Test the `AsyncESDataBackend.list` method given `new` argument set to True,
    should log a warning message.
    """
    backend = async_es_backend()

    async def mock_get(*args, **kwargs):
        return {}

    monkeypatch.setattr(backend.client.indices, "get", mock_get)
    with caplog.at_level(logging.WARNING):
        result = [statement async for statement in backend.list(new=True)]
        assert not list(result)

    assert (
        "ralph.backends.data.async_es",
        logging.WARNING,
        "The `new` argument is ignored",
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_list_with_details(async_es_backend, monkeypatch):
    """Test the `AsyncESDataBackend.list` method with `details` set to `True`."""
    indices = {"index_1": {"info_1": "foo"}, "index_2": {"info_2": "baz"}}

    async def mock_get(index):
        """Mocks the AsyncES.client.indices.get method returning a dictionary."""
        assert index == "target_index*"
        return indices

    backend = async_es_backend()
    monkeypatch.setattr(backend.client.indices, "get", mock_get)
    result = [
        statement async for statement in backend.list("target_index*", details=True)
    ]
    assert isinstance(result, Iterable)
    assert list(result) == [
        {"index_1": {"info_1": "foo"}},
        {"index_2": {"info_2": "baz"}},
    ]

    await backend.close()


@pytest.mark.parametrize(
    "exception, error",
    [
        (ApiError("", ApiResponseMeta(*([None] * 5)), None), r"ApiError\(None, ''\)"),
        (ESConnectionError(""), "Connection error"),
    ],
)
@pytest.mark.anyio
async def test_backends_data_async_es_read_with_failure(  # noqa: PLR0913
    exception, error, es, async_es_backend, caplog, monkeypatch
):
    """Test the `AsyncESDataBackend.read` method, given a request failure, should
    raise a `BackendException`.
    """

    def mock_async_es_search_open_pit(**kwargs):
        """Mock the AsyncES.client.search and open_point_in_time methods always raising
        an exception.
        """
        raise exception

    backend = async_es_backend()

    # Search failure.
    monkeypatch.setattr(backend.client, "search", mock_async_es_search_open_pit)
    with pytest.raises(
        BackendException, match=f"Failed to execute Elasticsearch query: {error}"
    ):
        with caplog.at_level(logging.ERROR):
            result = [statement async for statement in backend.read()]
            next(iter(result))

    assert (
        "ralph.backends.data.async_es",
        logging.ERROR,
        "Failed to execute Elasticsearch query: %s" % error.replace("\\", ""),
    ) in caplog.record_tuples

    # Open point in time failure.
    monkeypatch.setattr(
        backend.client, "open_point_in_time", mock_async_es_search_open_pit
    )
    with pytest.raises(
        BackendException, match=f"Failed to open Elasticsearch point in time: {error}"
    ):
        with caplog.at_level(logging.ERROR):
            result = [statement async for statement in backend.read()]
            next(iter(result))

    error = error.replace("\\", "")
    assert (
        "ralph.backends.data.async_es",
        logging.ERROR,
        "Failed to open Elasticsearch point in time: %s" % error.replace("\\", ""),
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_read_with_ignore_errors(
    es, async_es_backend, monkeypatch, caplog
):
    """Test the `AsyncESDataBackend.read` method, given `ignore_errors` set to `False`,
    should raise a BackendException if a JSON parsing error occurs.

    Given `ignore_errors` set to `False`, the `read` method should log a warning
    message instead.
    """

    async def mock_async_es_search(**kwargs):
        return {"hits": {"hits": [{"foo": 1j, "sort": []}]}}

    backend = async_es_backend()
    monkeypatch.setattr(backend.client, "search", mock_async_es_search)
    error = (
        "Failed to encode JSON: Object of type complex is not JSON serializable, "
        "for document: {'foo': 1j, 'sort': []}, at line 0"
    )
    with pytest.raises(BackendException, match=re.escape(error)):
        with caplog.at_level(logging.ERROR):
            _ = [x async for x in backend.read(ignore_errors=False, raw_output=True)]

    assert (
        "ralph.utils",
        logging.ERROR,
        error,
    ) in caplog.record_tuples

    with caplog.at_level(logging.WARNING):
        _ = [x async for x in backend.read(ignore_errors=True, raw_output=True)]

    assert (
        "ralph.utils",
        logging.WARNING,
        error,
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_es_read_with_raw_ouput(
    prefetch, es, async_es_backend
):
    """Test the `AsyncESDataBackend.read` method with `raw_output` set to `True`."""

    backend = async_es_backend()
    documents = [{"id": idx, "timestamp": now()} for idx in range(10)]
    assert await backend.write(documents) == 10
    hits = [
        statement
        async for statement in backend.read(raw_output=True, prefetch=prefetch)
    ]
    for i, hit in enumerate(hits):
        assert isinstance(hit, bytes)
        assert json.loads(hit).get("_source") == documents[i]

    await backend.close()


@pytest.mark.anyio
@pytest.mark.parametrize("prefetch", [1, 10])
async def test_backends_data_async_es_read_without_raw_ouput(
    prefetch, es, async_es_backend
):
    """Test the `AsyncESDataBackend.read` method with `raw_output` set to `False`."""

    backend = async_es_backend()
    documents = [{"id": idx, "timestamp": now()} for idx in range(10)]
    assert await backend.write(documents) == 10
    hits = [statement async for statement in backend.read(prefetch=prefetch)]
    for i, hit in enumerate(hits):
        assert isinstance(hit, dict)
        assert hit.get("_source") == documents[i]

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_read_with_query(es, async_es_backend, caplog):
    """Test the `AsyncESDataBackend.read` method with a query."""

    backend = async_es_backend()
    documents = [{"id": idx, "timestamp": now(), "modulo": idx % 2} for idx in range(5)]
    assert await backend.write(documents) == 5
    # Find every even item.
    query = ESQuery(query={"term": {"modulo": 0}})
    results = [statement async for statement in backend.read(query=query)]
    assert len(results) == 3
    assert results[0]["_source"]["id"] == 0
    assert results[1]["_source"]["id"] == 2
    assert results[2]["_source"]["id"] == 4

    # Find the first two even items.
    query = ESQuery(query={"term": {"modulo": 0}}, size=2)
    results = [statement async for statement in backend.read(query=query)]
    assert len(results) == 2
    assert results[0]["_source"]["id"] == 0
    assert results[1]["_source"]["id"] == 2

    # Find the first ten even items although there are only three available.
    query = ESQuery(query={"term": {"modulo": 0}}, size=10)
    results = [statement async for statement in backend.read(query=query)]
    assert len(results) == 3
    assert results[0]["_source"]["id"] == 0
    assert results[1]["_source"]["id"] == 2
    assert results[2]["_source"]["id"] == 4

    # Find every odd item.
    query = ESQuery(query={"term": {"modulo": 1}})
    results = [statement async for statement in backend.read(query=query)]
    assert len(results) == 2
    assert results[0]["_source"]["id"] == 1
    assert results[1]["_source"]["id"] == 3

    # Find every odd item with a json query string.
    query = ESQuery.from_string(json.dumps({"query": {"term": {"modulo": 1}}}))
    results = [statement async for statement in backend.read(query=query)]
    assert len(results) == 2
    assert results[0]["_source"]["id"] == 1
    assert results[1]["_source"]["id"] == 3

    # Find documents with ID equal to one or five.
    query = "id:(1 OR 5)"
    with caplog.at_level(logging.INFO):
        query = ESQuery.from_string(query)
        results = [statement async for statement in backend.read(query=query)]
    assert len(results) == 1
    assert results[0]["_source"]["id"] == 1
    assert (
        "ralph.backends.data.es",
        logging.INFO,
        "Fallback to Lucene Query as the query is not an ESQuery: id:(1 OR 5)",
    ) in caplog.record_tuples

    # Check query argument type
    with pytest.raises(
        BackendParameterException,
        match="'query' argument is expected to be a ESQuery instance",
    ):
        with caplog.at_level(logging.ERROR):
            _ = [
                statement
                async for statement in backend.read(query={"not_query": "foo"})
            ]

    assert (
        "ralph.backends.data.base",
        logging.ERROR,
        "The 'query' argument is expected to be a ESQuery instance",
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_concurrency(
    async_es_backend, monkeypatch
):
    """Test the `AsyncESDataBackend.write` method, given `concurrency` set,
    should pass the `concurrency` value to `AsyncWritable.write`.
    """

    async def mock_write(  # noqa: PLR0913
        self, data, target, chunk_size, ignore_errors, operation_type, concurrency
    ):
        """Mock the AsyncWritable `write` method."""
        assert concurrency == 4
        return 3

    backend = async_es_backend()
    monkeypatch.setattr(AsyncWritable, "write", mock_write)
    assert await backend.write([b"bar"], concurrency=4) == 3


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_create_operation(
    es, async_es_backend, caplog
):
    """Test the `AsyncESDataBackend.write` method, given an `CREATE` `operation_type`,
    should insert the target documents with the provided data.
    """

    backend = async_es_backend()
    assert len([statement async for statement in backend.read()]) == 0

    # Given an empty data iterator, the write method should return 0 and log a message.
    data = []
    with caplog.at_level(logging.INFO):
        assert await backend.write(data, operation_type=BaseOperationType.CREATE) == 0

    assert (
        "ralph.backends.data.base",
        logging.INFO,
        "Data Iterator is empty; skipping write to target",
    ) in caplog.record_tuples

    # Given an iterator with multiple documents, the write method should write the
    # documents to the default target index.
    data = ({"value": str(idx)} for idx in range(9))
    with caplog.at_level(logging.DEBUG):
        assert (
            await backend.write(
                data, chunk_size=5, operation_type=BaseOperationType.CREATE
            )
            == 9
        )

    write_records = 0
    for record in caplog.record_tuples:
        if re.match(r"^Wrote 1 document \[action: \{.*\}\]$", record[2]):
            write_records += 1
    assert write_records == 9

    assert (
        "ralph.backends.data.async_es",
        logging.INFO,
        "Finished writing 9 documents with success",
    ) in caplog.record_tuples

    hits = [statement async for statement in backend.read()]
    assert [hit["_source"] for hit in hits] == [{"value": str(idx)} for idx in range(9)]

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_delete_operation(
    es,
    async_es_backend,
):
    """Test the `AsyncESDataBackend.write` method, given a `DELETE` `operation_type`,
    should remove the target documents.
    """

    backend = async_es_backend()
    data = [{"id": idx, "value": str(idx)} for idx in range(10)]

    assert len([statement async for statement in backend.read()]) == 0
    assert await backend.write(data, chunk_size=5) == 10

    data = [{"id": idx} for idx in range(3)]

    assert (
        await backend.write(data, chunk_size=5, operation_type=BaseOperationType.DELETE)
        == 3
    )

    hits = [statement async for statement in backend.read()]
    assert len(hits) == 7
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(3, 10))

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_update_operation(
    es,
    async_es_backend,
):
    """Test the `AsyncESDataBackend.write` method, given an `UPDATE`
    `operation_type`, should overwrite the target documents with the provided data.
    """

    backend = async_es_backend()
    data = BytesIO(
        "\n".join(
            [json.dumps({"id": idx, "value": str(idx)}) for idx in range(10)]
        ).encode("utf8")
    )

    assert len([statement async for statement in backend.read()]) == 0
    assert await backend.write(data, chunk_size=5) == 10

    hits = [statement async for statement in backend.read()]
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
        await backend.write(data, chunk_size=5, operation_type=BaseOperationType.UPDATE)
        == 10
    )

    hits = [statement async for statement in backend.read()]
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))
    assert sorted([hit["_source"]["value"] for hit in hits]) == [
        str(x + 10) for x in range(10)
    ]

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_append_operation(
    async_es_backend, caplog
):
    """Test the `AsyncESDataBackend.write` method, given an `APPEND` `operation_type`,
    should raise a `BackendParameterException`.
    """
    backend = async_es_backend()
    msg = "Append operation_type is not allowed"
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.write(data=[{}], operation_type=BaseOperationType.APPEND)

    assert (
        "ralph.backends.data.base",
        logging.ERROR,
        "Append operation_type is not allowed",
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_target(es, async_es_backend):
    """Test the `AsyncESDataBackend.write` method, given a target index, should insert
    documents to the corresponding index.
    """

    backend = async_es_backend()

    def get_data():
        """Yield data."""
        yield {"value": "1"}
        yield {"value": "2"}

    # Create second Elasticsearch index.
    for _ in get_es_fixture(index=ES_TEST_FORWARDING_INDEX):
        # Both indexes should be empty.
        assert len([statement async for statement in backend.read()]) == 0
        assert (
            len(
                [
                    statement
                    async for statement in backend.read(target=ES_TEST_FORWARDING_INDEX)
                ]
            )
            == 0
        )

        # Write to forwarding index.
        assert await backend.write(get_data(), target=ES_TEST_FORWARDING_INDEX) == 2

        hits = [statement async for statement in backend.read()]
        hits_with_target = [
            statement
            async for statement in backend.read(target=ES_TEST_FORWARDING_INDEX)
        ]
        # No documents should be inserted into the default index.
        assert not hits
        # Documents should be inserted into the target index.
        assert [hit["_source"] for hit in hits_with_target] == [
            {"value": "1"},
            {"value": "2"},
        ]

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_without_ignore_errors(
    es, async_es_backend, caplog
):
    """Test the `AsyncESDataBackend.write` method with `ignore_errors` set to `False`,
    given badly formatted data, should raise a `BackendException`.
    """

    data = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    data[4].update({"count": "wrong"})

    backend = async_es_backend()
    assert len([statement async for statement in backend.read()]) == 0

    # By default, we should raise an error and stop the importation.
    msg = (
        r"1 document\(s\) failed to index. "
        r"\[\{'index': \{'_index': 'test-index-foo', '_id': '4', 'status': 400, 'error'"
        r": \{'type': 'document_parsing_exception', 'reason': \"\[1:17\] failed to parse field "
        r"\[count\] of type \[long\] in document with id '4'. Preview of field's value:"
        r" 'wrong'\", 'caused_by': \{'type': 'illegal_argument_exception', 'reason': "
        r"'For input string: \"wrong\"'\}\}, 'data': \{'id': 4, 'count': 'wrong'\}\}\}"
        r"\] Total succeeded writes: 5"
    )
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.write(data, chunk_size=2)

    assert (
        "ralph.backends.data.async_es",
        logging.ERROR,
        msg.replace("\\", ""),
    ) in caplog.record_tuples

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = [statement async for statement in backend.read()]
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
        r"for document: b'This is invalid JSON', at line 1"
    )
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.write(data, chunk_size=2)

    assert (
        "ralph.utils",
        logging.ERROR,
        msg.replace("\\", ""),
    ) in caplog.record_tuples

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = [statement async for statement in backend.read()]
    assert len(hits) == 5

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_ignore_errors(
    es, async_es_backend, caplog
):
    """Test the `AsyncESDataBackend.write` method with `ignore_errors` set to `True`,
    given badly formatted data, should should skip the invalid data.
    """

    msg = (
        "Failed to decode JSON: Expecting value: line 1 column 1 (char 0), "
        "for document: b'This is invalid JSON', at line 1"
    )
    records = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    records[2].update({"count": "wrong"})

    backend = async_es_backend()
    assert len([statement async for statement in backend.read()]) == 0

    assert await backend.write(records, chunk_size=2, ignore_errors=True) == 9

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = [statement async for statement in backend.read()]
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
    with caplog.at_level(logging.WARNING):
        assert await backend.write(data, chunk_size=2, ignore_errors=True) == 2

    es.indices.refresh(index=ES_TEST_INDEX)
    hits = [statement async for statement in backend.read()]
    assert len(hits) == 11
    assert [hit["_source"] for hit in hits[9:]] == [{"foo": "bar"}, {"foo": "baz"}]

    assert (
        "ralph.utils",
        logging.WARNING,
        msg,
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_async_es_write_with_datastream(
    es_data_stream, async_es_backend
):
    """Test the `AsyncESDataBackend.write` method using a configured data stream."""

    data = [{"id": idx, "@timestamp": datetime.now().isoformat()} for idx in range(10)]
    backend = async_es_backend()
    assert len([statement async for statement in backend.read()]) == 0
    assert (
        await backend.write(data, chunk_size=5, operation_type=BaseOperationType.CREATE)
        == 10
    )

    hits = [statement async for statement in backend.read()]
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))

    await backend.close()


@pytest.mark.anyio
async def test_backends_data_es_close_with_failure(async_es_backend, monkeypatch):
    """Test the `AsyncESDataBackend.close` method."""

    backend = async_es_backend()

    async def mock_connection_error():
        """ES client close mock that raises a connection error."""
        raise ESConnectionError("", (Exception("Mocked connection error"),))

    monkeypatch.setattr(backend.client, "close", mock_connection_error)

    with pytest.raises(BackendException, match="Failed to close Elasticsearch client"):
        await backend.close()


@pytest.mark.anyio
async def test_backends_data_es_close(async_es_backend, caplog):
    """Test the `AsyncESDataBackend.close` method."""

    # No client instantiated
    backend = async_es_backend()
    await backend.close()
    backend._client = None
    with caplog.at_level(logging.WARNING):
        await backend.close()

    assert (
        "ralph.backends.data.async_es",
        logging.WARNING,
        "No backend client to close.",
    ) in caplog.record_tuples
