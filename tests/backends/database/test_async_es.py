"""Tests for Ralph es database backend."""

import json
import logging
import random
import sys
from collections.abc import Iterable
from datetime import datetime
from io import StringIO
from pathlib import Path

import pytest
from elastic_transport import ApiResponseMeta
from elasticsearch import ApiError, AsyncElasticsearch
from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch.client import CatClient
from elasticsearch.helpers import async_bulk

from ralph.backends.database.async_es import AsyncESDatabase
from ralph.backends.database.base import DatabaseStatus, StatementParameters
from ralph.backends.database.es import ESQuery
from ralph.conf import ESClientOptions, settings
from ralph.exceptions import BackendException, BackendParameterException

from tests.fixtures.backends import (
    ASYNC_ES_TEST_FORWARDING_INDEX,
    ASYNC_ES_TEST_HOSTS,
    ASYNC_ES_TEST_INDEX,
)


@pytest.mark.anyio
async def test_backends_database_async_es_database_instantiation(async_es):
    """Tests the async ES backend instantiation."""
    # pylint: disable=invalid-name,unused-argument,protected-access

    assert AsyncESDatabase.name == "async_es"
    assert AsyncESDatabase.query_model == ESQuery

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS,
        index=ASYNC_ES_TEST_INDEX,
    )

    # When running locally host is 'elasticsearch', while it's localhost when
    # running from the CI
    assert any(
        (
            "http://elasticsearch:9200" in database._hosts,
            "http://localhost:9201" in database._hosts,
        )
    )
    assert database.index == ASYNC_ES_TEST_INDEX
    assert isinstance(database.client, AsyncElasticsearch)
    assert database.op_type == "index"

    for op_type in ("index", "create", "delete", "update"):
        database = AsyncESDatabase(
            hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX, op_type=op_type
        )
        assert database.op_type == op_type

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_database_instantiation_with_forbidden_op_type(
    async_es,
):
    """Tests the ES backend instantiation with an op_type that is not allowed."""
    # pylint: disable=invalid-name,unused-argument,protected-access

    with pytest.raises(BackendParameterException):
        database = AsyncESDatabase(
            hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX, op_type="foo"
        )
        await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_client_kwargs(async_es, fs):
    """Tests the async ES backend client instantiation using client_options that must be
    passed to the http(s) connection pool.
    """
    # pylint: disable=invalid-name,unused-argument,protected-access

    ca_certs_dir = "/path/to/ca/bundle"
    fs.create_dir(ca_certs_dir)

    database = AsyncESDatabase(
        hosts=[
            "https://elasticsearch:9200",
        ],
        index=ASYNC_ES_TEST_INDEX,
        client_options=ESClientOptions(
            ca_certs=ca_certs_dir,
            verify_certs=True,
        ),
    )

    assert database.client.transport.node_pool.get().config.ca_certs == Path(
        "/path/to/ca/bundle"
    )

    assert database.client.transport.node_pool.get().config.verify_certs is True

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_to_documents_method(async_es):
    """Tests to_documents method."""
    # pylint: disable=invalid-name,unused-argument

    # Create stream data
    stream = StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    stream.seek(0)

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS,
        index=ASYNC_ES_TEST_INDEX,
    )
    documents = database.to_documents(stream, lambda item: item.get("id"))
    assert isinstance(documents, Iterable)

    documents = list(documents)
    assert len(documents) == 10
    assert documents == [
        {
            "_index": database.index,
            "_id": idx,
            "_op_type": "index",
            "_source": {"id": idx},
        }
        for idx in range(10)
    ]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_to_documents_method_with_create_op_type(
    async_es,
):
    """Tests to_documents method using the create op_type."""
    # pylint: disable=invalid-name,unused-argument

    # Create stream data
    stream = StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    stream.seek(0)

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX, op_type="create"
    )
    documents = database.to_documents(stream, lambda item: item.get("id"))
    assert isinstance(documents, Iterable)

    documents = list(documents)
    assert len(documents) == 10
    assert documents == [
        {
            "_index": database.index,
            "_id": idx,
            "_op_type": "create",
            "_source": {"id": idx},
        }
        for idx in range(10)
    ]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_get_method(async_es):
    """Tests async ES get method."""
    # pylint: disable=invalid-name

    # Insert documents
    await async_bulk(
        async_es,
        (
            {"_index": ASYNC_ES_TEST_INDEX, "_id": idx, "_source": {"id": idx}}
            for idx in range(10)
        ),
    )
    # As we async_bulk insert documents, the index needs to be refreshed before making
    # queries.
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS,
        index=ASYNC_ES_TEST_INDEX,
    )

    expected = [{"id": idx} for idx in range(10)]
    assert [result.get("_source") async for result in database.get()] == expected

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_get_method_with_a_custom_query(async_es):
    """Tests async ES get method with a custom query."""
    # pylint: disable=invalid-name

    # Insert documents
    await async_bulk(
        async_es,
        (
            {
                "_index": ASYNC_ES_TEST_INDEX,
                "_id": idx,
                "_source": {"id": idx, "modulo": idx % 2},
            }
            for idx in range(10)
        ),
    )
    # As we async_bulk insert documents, the index needs to be refreshed before making
    # queries.
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS,
        index=ASYNC_ES_TEST_INDEX,
    )

    # Find every even item
    query = ESQuery(query={"query": {"term": {"modulo": 0}}})
    results = [result async for result in database.get(query=query)]
    assert len(results) == 5
    assert results[0]["_source"]["id"] == 0
    assert results[1]["_source"]["id"] == 2
    assert results[2]["_source"]["id"] == 4
    assert results[3]["_source"]["id"] == 6
    assert results[4]["_source"]["id"] == 8

    # Check query argument type
    with pytest.raises(
        BackendParameterException,
        match="'query' argument is expected to be a ESQuery instance.",
    ):
        results = [result async for result in database.get(query="foo")]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_put_method(async_es, fs, monkeypatch):
    """Tests async ES put method."""
    # pylint: disable=invalid-name

    # Prepare fake file system
    fs.create_dir(str(settings.APP_DIR))
    # Force Path instantiation with fake FS
    history_file = Path(settings.HISTORY_FILE)
    assert not history_file.exists()

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    )

    assert len((await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]) == 0

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS,
        index=ASYNC_ES_TEST_INDEX,
    )
    success_count = await database.put(sys.stdin, chunk_size=5)

    # As we async_bulk insert documents, the index needs to be refreshed before making
    # queries.
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)

    hits = (await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]
    assert len(hits) == 10
    assert success_count == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_put_method_with_update_op_type(
    async_es, fs, monkeypatch
):
    """Tests async ES put method using the update op_type."""
    # pylint: disable=invalid-name

    # Prepare fake file system
    fs.create_dir(settings.APP_DIR)
    # Force Path instantiation with fake FS
    history_file = Path(settings.HISTORY_FILE)
    assert not history_file.exists()

    monkeypatch.setattr(
        "sys.stdin",
        StringIO(
            "\n".join([json.dumps({"id": idx, "value": str(idx)}) for idx in range(10)])
        ),
    )

    assert len((await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]) == 0

    database = AsyncESDatabase(hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX)
    await database.put(sys.stdin, chunk_size=5)

    # As we async_bulk insert documents, the index needs to be refreshed before making
    # queries.
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)

    hits = (await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))
    assert sorted([hit["_source"]["value"] for hit in hits]) == list(
        map(str, range(10))
    )

    monkeypatch.setattr(
        "sys.stdin",
        StringIO(
            "\n".join(
                [json.dumps({"id": idx, "value": str(10 + idx)}) for idx in range(10)]
            )
        ),
    )

    await database.close()

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX, op_type="update"
    )
    success_count = await database.put(sys.stdin, chunk_size=5)

    # As we async_bulk insert documents, the index needs to be refreshed before making
    # queries.
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)

    hits = (await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]
    assert len(hits) == 10
    assert success_count == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))
    assert sorted([hit["_source"]["value"] for hit in hits]) == list(
        map(lambda x: str(x + 10), range(10))
    )

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_put_with_bad_data_raises_a_backend_exception(
    async_es, fs, monkeypatch
):
    """Tests async ES put method with badly formatted data."""
    # pylint: disable=invalid-name,unused-argument

    records = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    records[4].update({"count": "wrong"})

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps(record) for record in records]))
    )

    assert len((await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]) == 0

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS,
        index=ASYNC_ES_TEST_INDEX,
    )

    # By default, we should raise an error and stop the importation
    msg = "\\('1 document\\(s\\) failed to index.', '5 succeeded writes'\\)"
    with pytest.raises(BackendException, match=msg) as exception_info:
        await database.put(sys.stdin, chunk_size=2)
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)
    hits = (await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]
    assert len(hits) == 5
    assert exception_info.value.args[-1] == "5 succeeded writes"
    assert sorted([hit["_source"]["id"] for hit in hits]) == [0, 1, 2, 3, 5]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_put_with_badly_formatted_data_in_force_mode(
    async_es, fs, monkeypatch
):
    """Tests async ES put method with badly formatted data when the
    force mode is active.
    """
    # pylint: disable=invalid-name,unused-argument

    records = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    records[2].update({"count": "wrong"})

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps(record) for record in records]))
    )

    assert len((await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]) == 0

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS,
        index=ASYNC_ES_TEST_INDEX,
    )
    # When forcing import, We expect the record with non expected type to have
    # been dropped
    await database.put(sys.stdin, chunk_size=5, ignore_errors=True)
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)
    hits = (await async_es.search(index=ASYNC_ES_TEST_INDEX))["hits"]["hits"]
    assert len(hits) == 9
    assert sorted([hit["_source"]["id"] for hit in hits]) == [
        i for i in range(10) if i != 2
    ]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_put_with_datastream(
    async_es_data_stream, fs, monkeypatch
):
    """Tests async ES put method when using a configured data stream."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr(
        "sys.stdin",
        StringIO(
            "\n".join(
                [
                    json.dumps({"id": idx, "@timestamp": datetime.now().isoformat()})
                    for idx in range(10)
                ]
            )
        ),
    )

    assert (
        len(
            (await async_es_data_stream.search(index=ASYNC_ES_TEST_INDEX))["hits"][
                "hits"
            ]
        )
        == 0
    )

    database = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX, op_type="create"
    )
    await database.put(sys.stdin, chunk_size=5)

    # As we async_bulk insert documents, the index needs to be refreshed before making
    # queries.
    await async_es_data_stream.indices.refresh(index=ASYNC_ES_TEST_INDEX)

    hits = (await async_es_data_stream.search(index=ASYNC_ES_TEST_INDEX))["hits"][
        "hits"
    ]
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_query_statements_with_pit_query_failure(
    monkeypatch, caplog, async_es
):
    """Tests the ES query_statements method, given a point in time query failure, should
    raise a BackendException and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_open_point_in_time(**_):
        """Mocks the AsyncElasticsearch.open_point_in_time method."""
        raise ValueError("ES failure")

    database = AsyncESDatabase(hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX)
    monkeypatch.setattr(database.client, "open_point_in_time", mock_open_point_in_time)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to open ElasticSearch point in time', 'ES failure'"
    with pytest.raises(BackendException, match=msg):
        await database.query_statements(StatementParameters())

    logger_name = "ralph.backends.database.async_es"
    msg = "Failed to open ElasticSearch point in time. ES failure"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_query_statements_with_search_query_failure(
    monkeypatch, caplog, async_es
):
    """Tests the async ES query_statements method, given a search query failure, should
    raise a BackendException and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_search(**_):
        """Mocks the AsyncElasticsearch.search method."""
        raise ApiError("Something is wrong", ApiResponseMeta(*([None] * 5)), None)

    database = AsyncESDatabase(hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX)
    monkeypatch.setattr(database.client, "search", mock_search)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute AsyncElasticsearch query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        await database.query_statements(StatementParameters())

    logger_name = "ralph.backends.database.async_es"
    msg = (
        "Failed to execute AsyncElasticsearch query. "
        "ApiError(None, 'Something is wrong')"
    )
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_query_stat_by_ids_with_search_query_failure(
    monkeypatch, caplog, async_es
):
    """Tests the async ES query_statements_by_ids method, given a search query failure,
    should raise a BackendException and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_search(**_):
        """Mocks the AsyncElasticsearch.search method."""
        raise ApiError("Something is wrong", ApiResponseMeta(*([None] * 5)), None)

    database = AsyncESDatabase(hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX)
    monkeypatch.setattr(database.client, "search", mock_search)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute AsyncElasticsearch query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        await database.query_statements_by_ids(StatementParameters())

    logger_name = "ralph.backends.database.async_es"
    msg = (
        "Failed to execute AsyncElasticsearch query. "
        "ApiError(None, 'Something is wrong')"
    )
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_query_statements_by_ids_with_multiple_indexes(
    async_es, async_es_forwarding
):
    """Tests the async ES query_statements_by_ids method, given a valid search
    query, should execute the query uniquely on the specified index and return the
    expected results.
    """
    # pylint: disable=invalid-name,use-implicit-booleaness-not-comparison

    # Insert documents
    index_1_document = {
        "_index": ASYNC_ES_TEST_INDEX,
        "_id": "1",
        "_source": {"id": "1"},
    }
    index_2_document = {
        "_index": ASYNC_ES_TEST_FORWARDING_INDEX,
        "_id": "2",
        "_source": {"id": "2"},
    }
    await async_bulk(async_es, [index_1_document])
    await async_bulk(async_es_forwarding, [index_2_document])

    # As we async_bulk insert documents, the index needs to be refreshed
    # before making queries
    await async_es.indices.refresh(index=ASYNC_ES_TEST_INDEX)
    await async_es_forwarding.indices.refresh(index=ASYNC_ES_TEST_FORWARDING_INDEX)

    # Instantiate ES Databases
    database = AsyncESDatabase(hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX)
    database_2 = AsyncESDatabase(
        hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_FORWARDING_INDEX
    )

    # Check the expected search query results
    index_1_document = dict(index_1_document, **{"_score": 1.0})
    index_2_document = dict(index_2_document, **{"_score": 1.0})
    assert await database.query_statements_by_ids(["1"]) == [index_1_document]
    assert await database.query_statements_by_ids(["2"]) == []
    assert await database_2.query_statements_by_ids(["1"]) == []
    assert await database_2.query_statements_by_ids(["2"]) == [index_2_document]

    await database.close()
    await database_2.close()


@pytest.mark.anyio
async def test_backends_database_async_es_status(async_es, monkeypatch):
    """Test the async ES status method."""
    # pylint: disable=invalid-name,unused-argument

    database = AsyncESDatabase(hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX)

    with monkeypatch.context() as mkpch:

        async def mock_async_health_ok(*args, **kwargs):
            return "1664532320 10:05:20 docker-cluster green 1 1 2 2 0 0 1 0 - 66.7%"

        mkpch.setattr(CatClient, "health", mock_async_health_ok)
        assert await database.status() == DatabaseStatus.OK

    with monkeypatch.context() as mkpch:

        async def mock_async_health_error(*args, **kwargs):
            return "1664532320 10:05:20 docker-cluster yellow 1 1 2 2 0 0 1 0 - 66.7%"

        mkpch.setattr(CatClient, "health", mock_async_health_error)
        assert await database.status() == DatabaseStatus.ERROR

    with monkeypatch.context() as mkpch:

        async def mock_connection_error(*args, **kwargs):
            """async ES client info mock that raises a connection error."""
            raise ESConnectionError("Mocked connection error")

        mkpch.setattr(AsyncElasticsearch, "info", mock_connection_error)
        assert await database.status() == DatabaseStatus.AWAY

    await database.close()


@pytest.mark.anyio
async def test_backends_database_async_es_close(async_es, monkeypatch, caplog):
    """Test the async ES close method."""
    # pylint: disable=invalid-name,unused-argument

    database = AsyncESDatabase(hosts=ASYNC_ES_TEST_HOSTS, index=ASYNC_ES_TEST_INDEX)

    await database.close()

    assert await database.status() == DatabaseStatus.ERROR

    # with pytest.raises(BackendException):
    await database.close()

    async def mock_close(**_):
        """Mocks the AsyncElasticsearch.close method."""
        raise ApiError("Something is wrong", ApiResponseMeta(*([None] * 5)), None)

    monkeypatch.setattr(database.client, "close", mock_close)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to close AsyncElasticsearch client', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        await database.close()
