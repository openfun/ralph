"""Tests for Ralph es database backend"""

import json
import random
import sys
from collections.abc import Iterable
from io import BytesIO, StringIO
from pathlib import Path

import pytest
from elasticsearch import Elasticsearch
from elasticsearch.helpers import BulkIndexError, bulk

from ralph.backends.database.es import ESDatabase
from ralph.defaults import APP_DIR, HISTORY_FILE

from tests.fixtures.backends import ES_TEST_HOSTS, ES_TEST_INDEX


def test_es_database_instanciation(es):
    """Test the ES backend instanciation"""
    # pylint: disable=invalid-name,unused-argument,protected-access

    assert ESDatabase.name == "es"

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


def test_to_documents_method(es):
    """Test to_documents method"""
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
        {"_index": database.index, "_id": idx, "_source": {"id": idx}}
        for idx in range(10)
    ]


def test_get_method(es, monkeypatch):
    """Test ES get method"""
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

    # Mock stdout stream
    class MockStdout:
        """A simple mock for sys.stdout.buffer"""

        buffer = BytesIO()

    mock_stdout = MockStdout()
    monkeypatch.setattr(sys, "stdout", mock_stdout)

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )
    database.get()

    mock_stdout.buffer.seek(0)
    documents = [json.loads(line) for line in mock_stdout.buffer.readlines()]
    assert documents == [{"id": idx} for idx in range(10)]


def test_put_method(es, fs, monkeypatch):
    """Test ES put method"""
    # pylint: disable=invalid-name

    # Prepare fake file system
    fs.create_dir(str(APP_DIR))
    # Force Path instanciation with fake FS
    history_file = Path(str(HISTORY_FILE))
    assert not history_file.exists()

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    )

    assert len(es.search(index=ES_TEST_INDEX)["hits"]["hits"]) == 0

    database = ESDatabase(
        hosts=ES_TEST_HOSTS,
        index=ES_TEST_INDEX,
    )
    database.put(chunk_size=5)

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 10
    assert sorted([hit["_source"]["id"] for hit in hits]) == list(range(10))


def test_put_with_badly_formatted_data_raises_a_bulkindexerror(es, fs, monkeypatch):
    """Test ES put method with badly formatted data"""
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

    # By default, we sould raise an error and stop the importation
    with pytest.raises(BulkIndexError):
        database.put(chunk_size=2)
    es.indices.refresh(index=ES_TEST_INDEX)
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 5
    assert sorted([hit["_source"]["id"] for hit in hits]) == [0, 1, 2, 3, 5]


def test_put_with_badly_formatted_data_in_force_mode(es, fs, monkeypatch):
    """Test ES put method with badly formatted data when the force mode is active"""
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
    database.put(chunk_size=5, ignore_errors=True)
    es.indices.refresh(index=ES_TEST_INDEX)
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 9
    assert sorted([hit["_source"]["id"] for hit in hits]) == [
        i for i in range(10) if i != 2
    ]
