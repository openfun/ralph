"""Tests for Ralph es database backend"""

import json
import sys
from collections.abc import Iterable
from io import BytesIO, StringIO
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

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


def test_write_method(es, fs, monkeypatch):
    """Test ES write method"""
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
