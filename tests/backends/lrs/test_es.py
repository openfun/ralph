"""Tests for Ralph Elasticsearch LRS backend."""

import logging
import re
from datetime import datetime

import pytest
from elastic_transport import ApiResponseMeta
from elasticsearch import ApiError
from elasticsearch.helpers import bulk

from ralph.backends.lrs.base import StatementParameters
from ralph.exceptions import BackendException

from tests.fixtures.backends import ES_TEST_FORWARDING_INDEX, ES_TEST_INDEX


@pytest.mark.parametrize(
    "params,expected_query",
    [
        # 0. Default query.
        (
            {},
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {"match_all": {}},
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "statementId"},
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {"bool": {"filter": [{"term": {"_id": "statementId"}}]}},
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 2. Query by statementId and agent with mbox IFI.
        (
            {"statementId": "statementId", "agent": {"mbox": "mailto:foo@bar.baz"}},
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"actor.mbox.keyword": "mailto:foo@bar.baz"}},
                        ]
                    }
                },
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 3. Query by statementId and agent with mbox_sha1sum IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"mbox_sha1sum": "a7a5b7462b862c8c8767d43d43e865ffff754a64"},
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {
                                "term": {
                                    "actor.mbox_sha1sum.keyword": (
                                        "a7a5b7462b862c8c8767d43d43e865ffff754a64"
                                    )
                                }
                            },
                        ]
                    }
                },
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 4. Query by statementId and agent with openid IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"openid": "http://toby.openid.example.org/"},
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {
                                "term": {
                                    "actor.openid.keyword": (
                                        "http://toby.openid.example.org/"
                                    )
                                }
                            },
                        ]
                    }
                },
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 5. Query by statementId and agent with account IFI.
        (
            {
                "statementId": "statementId",
                "agent": {
                    "account__home_page": "http://www.example.com",
                    "account__name": "13936749",
                },
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"actor.account.name.keyword": ("13936749")}},
                            {
                                "term": {
                                    "actor.account.homePage.keyword": (
                                        "http://www.example.com"
                                    )
                                }
                            },
                        ]
                    }
                },
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 6. Query by verb and activity.
        (
            {
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "term": {
                                    "verb.id.keyword": (
                                        "http://adlnet.gov/expapi/verbs/attended"
                                    )
                                }
                            },
                            {"term": {"object.objectType.keyword": "Activity"}},
                            {
                                "term": {
                                    "object.id.keyword": (
                                        "http://www.example.com/meetings/34534"
                                    )
                                }
                            },
                        ]
                    }
                },
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 7. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "range": {
                                    "timestamp": {
                                        "gt": datetime.fromisoformat(
                                            "2021-06-24T00:00:20.194929+00:00"
                                        )
                                    }
                                }
                            },
                            {
                                "range": {
                                    "timestamp": {
                                        "lte": datetime.fromisoformat(
                                            "2023-06-24T00:00:20.194929+00:00"
                                        )
                                    }
                                }
                            },
                        ]
                    }
                },
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 8. Query with pagination and pit_id.
        (
            {"search_after": "1686557542970|0", "pit_id": "46ToAwMDaWR5BXV1a"},
            {
                "pit": {"id": "46ToAwMDaWR5BXV1a", "keep_alive": None},
                "query": {"match_all": {}},
                "query_string": None,
                "search_after": ["1686557542970", "0"],
                "size": None,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 9. Query ignoring statement sort order.
        (
            {"ignore_order": True},
            {
                "pit": {"id": None, "keep_alive": None},
                "query": {"match_all": {}},
                "query_string": None,
                "search_after": None,
                "size": None,
                "sort": "_shard_doc",
                "track_total_hits": False,
            },
        ),
    ],
)
def test_backends_lrs_es_lrs_backend_query_statements_query(
    params, expected_query, es_lrs_backend, monkeypatch
):
    """Test the `ESLRSBackend.query_statements` method, given valid statement
    parameters, should produce the expected Elasticsearch query.
    """

    def mock_read(query, chunk_size):
        """Mock the `ESLRSBackend.read` method."""
        assert query.dict() == expected_query
        assert chunk_size == expected_query.get("size")
        query.pit.id = "foo_pit_id"
        query.search_after = ["bar_search_after", "baz_search_after"]
        return []

    backend = es_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)
    result = backend.query_statements(StatementParameters(**params))
    assert not result.statements
    assert result.pit_id == "foo_pit_id"
    assert result.search_after == "bar_search_after|baz_search_after"

    backend.close()


def test_backends_lrs_es_lrs_backend_query_statements(es, es_lrs_backend):
    """Test the `ESLRSBackend.query_statements` method, given a query,
    should return matching statements.
    """
    # pylint: disable=invalid-name,unused-argument
    # Instantiate ESLRSBackend.
    backend = es_lrs_backend()
    # Insert documents.
    documents = [{"id": "2", "timestamp": "2023-06-24T00:00:20.194929+00:00"}]
    assert backend.write(documents) == 1

    # Check the expected search query results.
    result = backend.query_statements(StatementParameters(limit=10))
    assert result.statements == documents
    assert re.match(r"[0-9]+\|0", result.search_after)

    backend.close()


def test_backends_lrs_es_lrs_backend_query_statements_with_search_query_failure(
    es, es_lrs_backend, monkeypatch, caplog
):
    """Test the `ESLRSBackend.query_statements`, given a search query failure, should
    raise a `BackendException` and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_read(**_):
        """Mock the Elasticsearch.read method."""
        raise BackendException("Query error")

    backend = es_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    msg = "Query error"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            backend.query_statements(StatementParameters())

    assert (
        "ralph.backends.lrs.es",
        logging.ERROR,
        "Failed to read from Elasticsearch",
    ) in caplog.record_tuples

    backend.close()


def test_backends_lrs_es_lrs_backend_query_statements_by_ids_with_search_query_failure(
    es, es_lrs_backend, monkeypatch, caplog
):
    """Test the `ESLRSBackend.query_statements_by_ids` method, given a search query
    failure, should raise a `BackendException` and log the error.
    """
    # pylint: disable=invalid-name,unused-argument

    def mock_search(**_):
        """Mock the Elasticsearch.search method."""
        raise ApiError("Query error", ApiResponseMeta(*([None] * 5)), None)

    backend = es_lrs_backend()
    monkeypatch.setattr(backend.client, "search", mock_search)

    msg = r"Failed to execute Elasticsearch query: ApiError\(None, 'Query error'\)"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            list(backend.query_statements_by_ids(StatementParameters()))

    assert (
        "ralph.backends.lrs.es",
        logging.ERROR,
        "Failed to read from Elasticsearch",
    ) in caplog.record_tuples

    backend.close()


def test_backends_lrs_es_lrs_backend_query_statements_by_ids_with_multiple_indexes(
    es, es_forwarding, es_lrs_backend
):
    """Test the `ESLRSBackend.query_statements_by_ids` method, given a valid search
    query, should execute the query only on the specified index and return the
    expected results.
    """
    # pylint: disable=invalid-name

    # Insert documents.
    index_1_document = {"_index": ES_TEST_INDEX, "_id": "1", "_source": {"id": "1"}}
    index_2_document = {
        "_index": ES_TEST_FORWARDING_INDEX,
        "_id": "2",
        "_source": {"id": "2"},
    }
    bulk(es, [index_1_document])
    bulk(es_forwarding, [index_2_document])

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)
    es_forwarding.indices.refresh(index=ES_TEST_FORWARDING_INDEX)

    # Instantiate ESLRSBackends.
    backend_1 = es_lrs_backend(index=ES_TEST_INDEX)
    backend_2 = es_lrs_backend(index=ES_TEST_FORWARDING_INDEX)

    # Check the expected search query results.
    index_1_document = {"id": "1"}
    index_2_document = {"id": "2"}
    assert list(backend_1.query_statements_by_ids(["1"])) == [index_1_document]
    assert not list(backend_1.query_statements_by_ids(["2"]))
    assert not list(backend_2.query_statements_by_ids(["1"]))
    assert list(backend_2.query_statements_by_ids(["2"])) == [index_2_document]

    backend_1.close()
    backend_2.close()
