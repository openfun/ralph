"""Tests for Ralph MongoDB LRS backend."""

import logging

import pytest
from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING

from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.exceptions import BackendException

from tests.fixtures.backends import MONGO_TEST_FORWARDING_COLLECTION


@pytest.mark.parametrize(
    "params,expected_query",
    [
        # 0. Default query.
        (
            {},
            {
                "filter": {},
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "statementId"},
            {
                "filter": {"_source.id": "statementId"},
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 2. Query by statementId and agent with mbox IFI.
        (
            {"statementId": "statementId", "agent": {"mbox": "mailto:foo@bar.baz"}},
            {
                "filter": {
                    "_source.id": "statementId",
                    "_source.actor.mbox": "mailto:foo@bar.baz",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 3. Query by statementId and agent with mbox_sha1sum IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"mbox_sha1sum": "a7a5b7462b862c8c8767d43d43e865ffff754a64"},
            },
            {
                "filter": {
                    "_source.id": "statementId",
                    "_source.actor.mbox_sha1sum": (
                        "a7a5b7462b862c8c8767d43d43e865ffff754a64"
                    ),
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 4. Query by statementId and agent with openid IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"openid": "http://toby.openid.example.org/"},
            },
            {
                "filter": {
                    "_source.id": "statementId",
                    "_source.actor.openid": "http://toby.openid.example.org/",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 5. Query by statementId and agent with account IFI.
        (
            {
                "statementId": "statementId",
                "agent": {
                    "account__name": "13936749",
                    "account__home_page": "http://www.example.com",
                },
            },
            {
                "filter": {
                    "_source.id": "statementId",
                    "_source.actor.account.name": "13936749",
                    "_source.actor.account.homePage": "http://www.example.com",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 6. Query by verb and activity.
        (
            {
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "filter": {
                    "_source.verb.id": "http://adlnet.gov/expapi/verbs/attended",
                    "_source.object.id": "http://www.example.com/meetings/34534",
                    "_source.object.objectType": "Activity",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 7. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "filter": {
                    "_source.timestamp": {
                        "$gt": "2021-06-24T00:00:20.194929+00:00",
                        "$lte": "2023-06-24T00:00:20.194929+00:00",
                    },
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 8. Query by timerange (with only until).
        (
            {
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "filter": {
                    "_source.timestamp": {
                        "$lte": "2023-06-24T00:00:20.194929+00:00",
                    },
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 9. Query with pagination.
        (
            {"search_after": "666f6f2d6261722d71757578", "pit_id": None},
            {
                "filter": {
                    "_id": {"$lt": ObjectId("666f6f2d6261722d71757578")},
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
                "query_string": None,
            },
        ),
        # 10. Query with pagination in ascending order.
        (
            {"search_after": "666f6f2d6261722d71757578", "ascending": True},
            {
                "filter": {
                    "_id": {"$gt": ObjectId("666f6f2d6261722d71757578")},
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.timestamp", ASCENDING),
                    ("_id", ASCENDING),
                ],
                "query_string": None,
            },
        ),
    ],
)
@pytest.mark.anyio
async def test_backends_lrs_async_mongo_lrs_backend_query_statements_query(
    params, expected_query, async_mongo_lrs_backend, monkeypatch
):
    """Test the `AsyncMongoLRSBackend.query_statements` method, given valid statement
    parameters, should produce the expected MongoDB query.
    """

    async def mock_read(query, chunk_size):
        """Mock the `AsyncMongoLRSBackend.read` method."""
        assert query.dict() == expected_query
        assert chunk_size == expected_query.get("limit")
        yield {"_id": "search_after_id", "_source": {}}

    backend = async_mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)
    result = await backend.query_statements(RalphStatementsQuery.construct(**params))
    assert result.statements == [{}]
    assert not result.pit_id
    assert result.search_after == "search_after_id"

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_lrs_backend_query_statements_with_success(
    mongo, async_mongo_lrs_backend
):
    """Test the `AsyncMongoLRSBackend.query_statements` method, given a valid search
    query, should return the expected statements.
    """
    # pylint: disable=unused-argument
    backend = async_mongo_lrs_backend()

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    meta = {
        "actor": {"account": {"name": "test_name", "homePage": "http://example.com"}},
        "verb": {"id": "verb_id"},
        "object": {"id": "http://example.com", "objectType": "Activity"},
    }
    documents = [
        {"id": "62b9ce922c26b46b68ffc68f", **timestamp, **meta},
        {"id": "62b9ce92fcde2b2edba56bf4", **timestamp, **meta},
    ]
    assert await backend.write(documents) == 2

    statement_parameters = RalphStatementsQuery.construct(
        statement_id="62b9ce922c26b46b68ffc68f",
        agent={
            "account__name": "test_name",
            "account__home_page": "http://example.com",
        },
        verb="verb_id",
        activity="http://example.com",
        since="2020-01-01T00:00:00.000000+00:00",
        until="2022-12-01T15:36:50",
        search_after="62b9ce922c26b46b68ffc68f",
        ascending=True,
        limit=25,
    )
    statement_query_result = await backend.query_statements(statement_parameters)

    assert statement_query_result.statements == [
        {"id": "62b9ce922c26b46b68ffc68f", **timestamp, **meta}
    ]


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_lrs_backend_query_statements_with_query_failure(
    async_mongo_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoLRSBackend.query_statements` method, given a search query
    failure, should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument

    msg = "Failed to execute MongoDB query: Something is wrong"

    async def mock_read(**_):
        """Mock the `MongoDataBackend.read` method always raising an Exception."""
        yield {"_source": {}}
        raise BackendException(msg)

    backend = async_mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            await backend.query_statements(RalphStatementsQuery.construct())

    assert (
        "ralph.backends.lrs.async_mongo",
        logging.ERROR,
        "Failed to read from async MongoDB",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_lrs_mongo_lrs_backend_query_statements_by_ids_query_failure(
    async_mongo_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoLRSBackend.query_statements_by_ids` method, given a search
    query failure, should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument

    msg = "Failed to execute MongoDB query: Something is wrong"

    async def mock_read(**_):
        """Mock the `AsyncMongoDataBackend.read` method always raising an Exception."""
        yield {"_source": {}}
        raise BackendException(msg)

    backend = async_mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            _ = [
                statement
                async for statement in backend.query_statements_by_ids(
                    RalphStatementsQuery.construct()
                )
            ]

    assert (
        "ralph.backends.lrs.async_mongo",
        logging.ERROR,
        "Failed to read from MongoDB",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_lrs_mongo_lrs_backend_query_statements_by_ids_two_collections(
    mongo, mongo_forwarding, async_mongo_lrs_backend
):
    """Tests the `AsyncMongoLRSBackend.query_statements_by_ids` method, given a valid
    search query, should execute the query only on the specified collection and return
    the expected results.
    """
    # pylint: disable=unused-argument

    # Instantiate Mongo Databases
    backend_1 = async_mongo_lrs_backend()
    backend_2 = async_mongo_lrs_backend(
        default_collection=MONGO_TEST_FORWARDING_COLLECTION
    )

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    assert await backend_1.write([{"id": "1", **timestamp}]) == 1
    assert await backend_2.write([{"id": "2", **timestamp}]) == 1

    # Check the expected search query results
    assert [
        statement async for statement in backend_1.query_statements_by_ids(["1"])
    ] == [{"id": "1", **timestamp}]
    assert not [
        statement async for statement in backend_1.query_statements_by_ids(["2"])
    ]
    assert not [
        statement async for statement in backend_2.query_statements_by_ids(["1"])
    ]
    assert [
        statement async for statement in backend_2.query_statements_by_ids(["2"])
    ] == [{"id": "2", **timestamp}]
