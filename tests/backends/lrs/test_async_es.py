"""Tests for Ralph Elasticsearch LRS backend."""

import logging
import re

import pytest
from elastic_transport import ApiResponseMeta
from elasticsearch import ApiError
from elasticsearch.helpers import bulk

from ralph.backends.lrs.async_es import AsyncESLRSBackend
from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.exceptions import BackendException

from tests.fixtures.backends import ES_TEST_FORWARDING_INDEX, ES_TEST_INDEX


def test_backends_lrs_async_es_default_instantiation(monkeypatch, fs):
    """Test the `ESLRSBackend` default instantiation."""
    fs.create_file(".env")
    monkeypatch.delenv("RALPH_BACKENDS__LRS__ES__DEFAULT_INDEX", raising=False)
    backend = AsyncESLRSBackend()
    assert backend.settings.DEFAULT_INDEX == "statements"

    monkeypatch.setenv("RALPH_BACKENDS__LRS__ES__DEFAULT_INDEX", "foo")
    backend = AsyncESLRSBackend()
    assert backend.settings.DEFAULT_INDEX == "foo"


@pytest.mark.parametrize(
    "params,expected_query",
    [
        # 0. Default query.
        (
            {},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {"match_all": {}},
                "search_after": None,
                "size": 0,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "statementId"},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {"bool": {"filter": [{"term": {"_id": "statementId"}}]}},
                "search_after": None,
                "size": 0,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 2. Query by statementId and agent with mbox IFI.
        (
            {"statementId": "statementId", "agent": {"mbox": "mailto:foo@bar.baz"}},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"actor.mbox.keyword": "mailto:foo@bar.baz"}},
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
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
                "q": None,
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
                "search_after": None,
                "size": 0,
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
                "q": None,
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
                "search_after": None,
                "size": 0,
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
                "q": None,
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
                "search_after": None,
                "size": 0,
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
                "q": None,
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
                "search_after": None,
                "size": 0,
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
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "range": {
                                    "timestamp": {
                                        "gt": "2021-06-24T00:00:20.194929+00:00"
                                    }
                                }
                            },
                            {
                                "range": {
                                    "timestamp": {
                                        "lte": "2023-06-24T00:00:20.194929+00:00"
                                    }
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 8. Query with pagination and pit_id.
        (
            {"search_after": "1686557542970|0", "pit_id": "46ToAwMDaWR5BXV1a"},
            {
                "pit": {"id": "46ToAwMDaWR5BXV1a", "keep_alive": None},
                "q": None,
                "query": {"match_all": {}},
                "search_after": ["1686557542970", "0"],
                "size": 0,
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 9. Query ignoring statement sort order.
        (
            {"ignore_order": True},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {"match_all": {}},
                "search_after": None,
                "size": 0,
                "sort": "_shard_doc",
                "track_total_hits": False,
            },
        ),
    ],
)
@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements_query(
    params, expected_query, async_es_lrs_backend, monkeypatch
):
    """Test the `AsyncESLRSBackend.query_statements` method, given valid statement
    parameters, should produce the expected Elasticsearch query.
    """

    async def mock_read(query, target, chunk_size):
        """Mock the `AsyncESLRSBackend.read` method."""
        assert query.model_dump() == expected_query
        assert chunk_size == expected_query.get("size")
        query.pit.id = "foo_pit_id"
        query.search_after = ["bar_search_after", "baz_search_after"]
        yield {"_source": {}}

    backend = async_es_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)
    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(**params)
    )
    assert result.statements == [{}]
    assert result.pit_id == "foo_pit_id"
    assert result.search_after == "bar_search_after|baz_search_after"

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements(es, async_es_lrs_backend):
    """Test the `AsyncESLRSBackend.query_statements` method, given a query,
    should return matching statements.
    """
    # Create a custom index
    custom_target = "custom-target"
    es.indices.create(index=custom_target)

    # Instantiate AsyncESLRSBackend.
    backend = async_es_lrs_backend()
    # Insert documents into default target.
    documents_default = [{"id": "2", "timestamp": "2023-06-24T00:00:20.194929+00:00"}]
    assert await backend.write(documents_default) == 1
    # Insert documents into custom target.
    documents_custom = [{"id": "3", "timestamp": "2023-05-25T00:00:20.194929+00:00"}]
    assert await backend.write(documents_custom, target=custom_target) == 1

    # Check the expected search query results.
    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(limit=10)
    )
    assert result.statements == documents_default
    assert re.match(r"[0-9]+\|0", result.search_after)

    # Check the expected search query results on custom target.
    result = await backend.query_statements(
        RalphStatementsQuery.construct(limit=10), target=custom_target
    )
    assert result.statements == documents_custom
    assert re.match(r"[0-9]+\|0", result.search_after)

    es.indices.delete(index=custom_target)
    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements_pit_query_failure(
    es, async_es_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncESLRSBackend.query_statements` method, given a point in time
    query failure, should raise a `BackendException` and log the error.
    """

    async def mock_read(**_):
        """Mock the Elasticsearch.read method."""
        yield {"_source": {}}
        raise BackendException("Query error")

    backend = async_es_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    msg = "Query error"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.query_statements(RalphStatementsQuery.model_construct())

    await backend.close()

    assert (
        "ralph.backends.lrs.async_es",
        logging.ERROR,
        "Failed to read from Elasticsearch",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_lrs_es_query_statements_by_ids_search_query_failure(
    es, async_es_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncESLRSBackend.query_statements_by_ids` method, given a search
    query failure, should raise a `BackendException` and log the error.
    """

    def mock_search(**_):
        """Mock the Elasticsearch.search method."""
        raise ApiError("Query error", ApiResponseMeta(*([None] * 5)), None)

    backend = async_es_lrs_backend()
    monkeypatch.setattr(backend.client, "search", mock_search)

    msg = r"Failed to execute Elasticsearch query: ApiError\(None, 'Query error'\)"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            _ = [
                statement
                async for statement in backend.query_statements_by_ids(
                    RalphStatementsQuery.model_construct()
                )
            ]

    await backend.close()

    assert (
        "ralph.backends.lrs.async_es",
        logging.ERROR,
        "Failed to read from Elasticsearch",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements_by_ids_many_indexes(
    es, es_forwarding, async_es_lrs_backend
):
    """Test the `AsyncESLRSBackend.query_statements_by_ids` method, given a valid
    search query, should execute the query uniquely on the specified index and return
    the expected results.
    """

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

    # Instantiate AsyncESLRSBackends.
    backend_1 = async_es_lrs_backend(index=ES_TEST_INDEX)
    backend_2 = async_es_lrs_backend(index=ES_TEST_FORWARDING_INDEX)

    # Check the expected search query results.
    index_1_document = {"id": "1"}
    index_2_document = {"id": "2"}
    assert [
        statement async for statement in backend_1.query_statements_by_ids(["1"])
    ] == [index_1_document]
    assert not [
        statement async for statement in backend_1.query_statements_by_ids(["2"])
    ]
    assert not [
        statement async for statement in backend_2.query_statements_by_ids(["1"])
    ]
    assert [
        statement async for statement in backend_2.query_statements_by_ids(["2"])
    ] == [index_2_document]

    # Check that backends can also read from another target
    assert [
        statement
        async for statement in backend_1.query_statements_by_ids(
            ["2"], target=ES_TEST_FORWARDING_INDEX
        )
    ] == [index_2_document]
    assert [
        statement
        async for statement in backend_2.query_statements_by_ids(
            ["1"], target=ES_TEST_INDEX
        )
    ] == [index_1_document]

    await backend_1.close()
    await backend_2.close()
