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
from elasticsearch import ApiError
from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch import Elasticsearch
from elasticsearch.client import CatClient
from elasticsearch.helpers import bulk

from ralph.backends.database.base import DatabaseStatus, RalphStatementsQuery
from ralph.backends.database.es import ESDatabase, ESQuery
from ralph.conf import ESClientOptions, settings
from ralph.exceptions import BackendException, BackendParameterException

from tests.fixtures.backends import (
    ES_TEST_FORWARDING_INDEX,
    ES_TEST_HOSTS,
    ES_TEST_INDEX,
)


def test_backends_database_es_database_instantiation(es):
    """Tests the ES backend instantiation."""
    # pylint: disable=invalid-name,unused-argument,protected-access

    assert ESDatabase.name == "es"
    assert ESDatabase.query_model == ESQuery

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )

    # When running locally host is 'elasticsearch', while it's localhost when
    # running from the CI
    assert any(
        (
            "http://elasticsearch:9200" in database._hosts,
            "http://localhost:9200" in database._hosts,
        )
    )
    assert database.index == ES_TEST_INDEX
    assert isinstance(database.client, Elasticsearch)
    assert database.op_type == "index"

    for op_type in ("index", "create", "delete", "update"):
        database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX, op_type=op_type)
        assert database.op_type == op_type


def test_backends_database_es_database_instantiation_with_forbidden_op_type(es):
    """Tests the ES backend instantiation with an op_type that is not allowed."""
    # pylint: disable=invalid-name,unused-argument,protected-access

    with pytest.raises(BackendParameterException):
        ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX, op_type="foo")


def test_backends_database_es_client_kwargs(es):
    """Tests the ES backend client instantiation using client_options that must be
    passed to the http(s) connection pool.
    """
    # pylint: disable=invalid-name,unused-argument,protected-access

    database = ESDatabase(
        hosts=[
            "https://elasticsearch:9200",
        ],
        index=ES_TEST_INDEX,
        client_options=ESClientOptions(
            ca_certs="/path/to/ca/bundle", verify_certs=True
        ),
    )

    assert database.client.transport.node_pool.get().config.ca_certs == Path(
        "/path/to/ca/bundle"
    )

    assert database.client.transport.node_pool.get().config.verify_certs is True


def test_backends_database_es_to_documents_method(es):
    """Tests to_documents method."""
    # pylint: disable=invalid-name,unused-argument

    # Create stream data
    stream = StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    stream.seek(0)

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
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


def test_backends_database_es_to_documents_method_with_create_op_type(es):
    """Tests to_documents method using the create op_type."""
    # pylint: disable=invalid-name,unused-argument

    # Create stream data
    stream = StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    stream.seek(0)

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX, op_type="create")
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


def test_backends_database_es_get_method(es):
    """Tests ES get method."""
    # pylint: disable=invalid-name

    # Insert documents
    bulk(
        es,
        (
            {"_index": ES_TEST_INDEX, "_id": idx, "_source": {"id": idx}}
            for idx in range(10)
        ),
    )
    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )

    expected = [{"id": idx} for idx in range(10)]
    assert list(map(lambda x: x.get("_source"), database.get())) == expected


def test_backends_database_es_get_method_with_a_custom_query(es):
    """Tests ES get method with a custom query."""
    # pylint: disable=invalid-name

    # Insert documents
    bulk(
        es,
        (
            {
                "_index": ES_TEST_INDEX,
                "_id": idx,
                "_source": {"id": idx, "modulo": idx % 2},
            }
            for idx in range(10)
        ),
    )
    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )

    # Find every even item
    query = ESQuery(query={"query": {"term": {"modulo": 0}}})
    results = list(database.get(query=query))
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
        list(database.get(query="foo"))


def test_backends_database_es_put_method(es, fs, monkeypatch):
    """Tests ES put method."""
    # pylint: disable=invalid-name

    # Prepare fake file system
    fs.create_dir(str(settings.APP_DIR))
    # Force Path instantiation with fake FS
    history_file = Path(settings.HISTORY_FILE)
    assert not history_file.exists()

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    )

    assert len(es.search(index=ES_TEST_INDEX)["hits"]["hits"]) == 0

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )
    success_count = database.put(sys.stdin, chunk_size=5)

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 10
    assert success_count == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))


def test_backends_database_es_put_method_with_update_op_type(es, fs, monkeypatch):
    """Tests ES put method using the update op_type."""
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

    assert len(es.search(index=ES_TEST_INDEX)["hits"]["hits"]) == 0

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX)
    database.put(sys.stdin, chunk_size=5)

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
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

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX, op_type="update")
    success_count = database.put(sys.stdin, chunk_size=5)

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 10
    assert success_count == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))
    assert sorted([hit["_source"]["value"] for hit in hits]) == list(
        map(lambda x: str(x + 10), range(10))
    )


def test_backends_database_es_put_with_badly_formatted_data_raises_a_backend_exception(
    es, fs, monkeypatch
):
    """Tests ES put method with badly formatted data."""
    # pylint: disable=invalid-name,unused-argument

    records = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    records[4].update({"count": "wrong"})

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps(record) for record in records]))
    )

    assert len(es.search(index=ES_TEST_INDEX)["hits"]["hits"]) == 0

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )

    # By default, we should raise an error and stop the importation
    msg = "\\('1 document\\(s\\) failed to index.', '5 succeeded writes'\\)"
    with pytest.raises(BackendException, match=msg) as exception_info:
        database.put(sys.stdin, chunk_size=2)
    es.indices.refresh(index=ES_TEST_INDEX)
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 5
    assert exception_info.value.args[-1] == "5 succeeded writes"
    assert sorted([hit["_source"]["id"] for hit in hits]) == [0, 1, 2, 3, 5]


def test_backends_database_es_put_with_badly_formatted_data_in_force_mode(
    es, fs, monkeypatch
):
    """Tests ES put method with badly formatted data when the force mode is active."""
    # pylint: disable=invalid-name,unused-argument

    records = [{"id": idx, "count": random.randint(0, 100)} for idx in range(10)]
    # Patch a record with a non-expected type for the count field (should be
    # assigned as long)
    records[2].update({"count": "wrong"})

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps(record) for record in records]))
    )

    assert len(es.search(index=ES_TEST_INDEX)["hits"]["hits"]) == 0

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )
    # When forcing import, We expect the record with non expected type to have
    # been dropped
    database.put(sys.stdin, chunk_size=5, ignore_errors=True)
    es.indices.refresh(index=ES_TEST_INDEX)
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 9
    assert sorted([hit["_source"]["id"] for hit in hits]) == [
        i for i in range(10) if i != 2
    ]


def test_backends_database_es_put_with_datastream(es_data_stream, fs, monkeypatch):
    """Tests ES put method when using a configured data stream."""
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

    assert len(es_data_stream.search(index=ES_TEST_INDEX)["hits"]["hits"]) == 0

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX, op_type="create")
    database.put(sys.stdin, chunk_size=5)

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es_data_stream.indices.refresh(index=ES_TEST_INDEX)

    hits = es_data_stream.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))


def test_backends_database_es_query_statements_with_pit_query_failure(
    monkeypatch, caplog, es
):
    """Tests the ES query_statements method, given a point in time query failure, should
    raise a BackendException and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_open_point_in_time(**_):
        """Mocks the Elasticsearch.open_point_in_time method."""
        raise ValueError("ES failure")

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX)
    monkeypatch.setattr(database.client, "open_point_in_time", mock_open_point_in_time)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to open ElasticSearch point in time', 'ES failure'"
    with pytest.raises(BackendException, match=msg):
        database.query_statements(RalphStatementsQuery.construct())

    logger_name = "ralph.backends.database.es"
    msg = "Failed to open ElasticSearch point in time. ES failure"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]


def test_backends_database_es_query_statements_with_search_query_failure(
    monkeypatch, caplog, es
):
    """Tests the ES query_statements method, given a search query failure, should
    raise a BackendException and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_search(**_):
        """Mocks the Elasticsearch.search method."""
        raise ApiError("Something is wrong", ApiResponseMeta(*([None] * 5)), None)

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX)
    monkeypatch.setattr(database.client, "search", mock_search)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute ElasticSearch query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        database.query_statements(RalphStatementsQuery.construct())

    logger_name = "ralph.backends.database.es"
    msg = "Failed to execute ElasticSearch query. ApiError(None, 'Something is wrong')"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]


def test_backends_database_es_query_statements_by_ids_with_search_query_failure(
    monkeypatch, caplog, es
):
    """Tests the ES query_statements_by_ids method, given a search query failure, should
    raise a BackendException and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_search(**_):
        """Mocks the Elasticsearch.search method."""
        raise ApiError("Something is wrong", ApiResponseMeta(*([None] * 5)), None)

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX)
    monkeypatch.setattr(database.client, "search", mock_search)

    caplog.set_level(logging.ERROR)

    msg = "'Failed to execute ElasticSearch query', 'Something is wrong'"
    with pytest.raises(BackendException, match=msg):
        database.query_statements_by_ids(RalphStatementsQuery())

    logger_name = "ralph.backends.database.es"
    msg = "Failed to execute ElasticSearch query. ApiError(None, 'Something is wrong')"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]


def test_backends_database_es_query_statements_by_ids_with_multiple_indexes(
    es, es_forwarding
):
    """Tests the ES query_statements_by_ids method, given a valid search
    query, should execute the query uniquely on the specified index and return the
    expected results.
    """
    # pylint: disable=invalid-name,use-implicit-booleaness-not-comparison

    # Insert documents
    index_1_document = {"_index": ES_TEST_INDEX, "_id": "1", "_source": {"id": "1"}}
    index_2_document = {
        "_index": ES_TEST_FORWARDING_INDEX,
        "_id": "2",
        "_source": {"id": "2"},
    }
    bulk(es, [index_1_document])
    bulk(es_forwarding, [index_2_document])

    # As we bulk insert documents, the index needs to be refreshed before making queries
    es.indices.refresh(index=ES_TEST_INDEX)
    es_forwarding.indices.refresh(index=ES_TEST_FORWARDING_INDEX)

    # Instantiate ES Databases
    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX)
    database_2 = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_FORWARDING_INDEX)

    # Check the expected search query results
    index_1_document = dict(index_1_document, **{"_score": 1.0})
    index_2_document = dict(index_2_document, **{"_score": 1.0})
    assert database.query_statements_by_ids(["1"]) == [index_1_document]
    assert database.query_statements_by_ids(["2"]) == []
    assert database_2.query_statements_by_ids(["1"]) == []
    assert database_2.query_statements_by_ids(["2"]) == [index_2_document]


def test_backends_database_es_status(es, monkeypatch):
    """Test the ES status method."""
    # pylint: disable=invalid-name,unused-argument

    database = ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_INDEX)

    with monkeypatch.context() as mkpch:
        mkpch.setattr(
            CatClient,
            "health",
            lambda client: (
                "1664532320 10:05:20 docker-cluster green 1 1 2 2 0 0 1 0 - 66.7%"
            ),
        )
        assert database.status() == DatabaseStatus.OK

    with monkeypatch.context() as mkpch:
        mkpch.setattr(
            CatClient,
            "health",
            lambda client: (
                "1664532320 10:05:20 docker-cluster yellow 1 1 2 2 0 0 1 0 - 66.7%"
            ),
        )
        assert database.status() == DatabaseStatus.ERROR

    with monkeypatch.context() as mkpch:

        def mock_connection_error(*args, **kwargs):
            """ES client info mock that raises a connection error."""
            raise ESConnectionError("Mocked connection error")

        mkpch.setattr(Elasticsearch, "info", mock_connection_error)
        assert database.status() == DatabaseStatus.AWAY
