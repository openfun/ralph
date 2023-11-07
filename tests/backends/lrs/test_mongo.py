"""Tests for Ralph MongoDB LRS backend."""

import logging

import pytest
from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING

from ralph.backends.lrs.base import AgentParameters, RalphStatementsQuery
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
def test_backends_lrs_mongo_lrs_backend_query_statements_query(
    params, expected_query, mongo_lrs_backend, monkeypatch
):
    """Test the `MongoLRSBackend.query_statements` method, given valid statement
    parameters, should produce the expected MongoDB query.
    """

    def mock_read(query, chunk_size):
        """Mock the `MongoLRSBackend.read` method."""
        assert query.dict() == expected_query
        assert chunk_size == expected_query.get("limit")
        return [{"_id": "search_after_id", "_source": {}}]

    backend = mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)
    result = backend.query_statements(RalphStatementsQuery.model_construct(**params))
    assert result.statements == [{}]
    assert not result.pit_id
    assert result.search_after == "search_after_id"
    backend.close()


def test_backends_lrs_mongo_lrs_backend_query_statements_with_success(
    mongo, mongo_lrs_backend
):
    """Test the `MongoLRSBackend.query_statements` method, given a valid search query,
    should return the expected statements.
    """
    # pylint: disable=unused-argument
    backend = mongo_lrs_backend()

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    meta = {
        "actor": {"account": {"name": "test_name", "homePage": "http://example.com"}},
        "verb": {"id": "https://xapi-example.com/verb-id"},
        "object": {"id": "http://example.com", "objectType": "Activity"},
    }
    documents = [
        {"id": "62b9ce922c26b46b68ffc68f", **timestamp, **meta},
        {"id": "62b9ce92fcde2b2edba56bf4", **timestamp, **meta},
    ]
    assert backend.write(documents) == 2

    statement_parameters = RalphStatementsQuery.model_construct(
        statementId="62b9ce922c26b46b68ffc68f",
        agent=AgentParameters.model_construct(
            account__name="test_name",
            account__home_page="http://example.com",
        ),
        verb="https://xapi-example.com/verb-id",
        activity="http://example.com",
        since="2020-01-01T00:00:00.000000+00:00",
        until="2022-12-01T15:36:50",
        search_after="62b9ce922c26b46b68ffc68f",
        ascending=True,
        limit=25,
    )
    statement_query_result = backend.query_statements(statement_parameters)

    assert statement_query_result.statements == [
        {"id": "62b9ce922c26b46b68ffc68f", **timestamp, **meta}
    ]
    backend.close()


def test_backends_lrs_mongo_lrs_backend_query_statements_with_query_failure(
    mongo_lrs_backend, monkeypatch, caplog
):
    """Test the `MongoLRSBackend.query_statements` method, given a search query failure,
    should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument

    msg = "Failed to execute MongoDB query: Something is wrong"

    def mock_read(**_):
        """Mock the `MongoDataBackend.read` method always raising an Exception."""
        yield {"_source": {}}
        raise BackendException(msg)

    backend = mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            backend.query_statements(RalphStatementsQuery.model_construct())

    assert (
        "ralph.backends.lrs.mongo",
        logging.ERROR,
        "Failed to read from MongoDB",
    ) in caplog.record_tuples
    backend.close()


def test_backends_lrs_mongo_lrs_backend_query_statements_by_ids_with_query_failure(
    mongo_lrs_backend, monkeypatch, caplog
):
    """Test the `MongoLRSBackend.query_statements_by_ids` method, given a search query
    failure, should raise a BackendException and log the error.
    """
    # pylint: disable=unused-argument

    msg = "Failed to execute MongoDB query: Something is wrong"

    def mock_read(**_):
        """Mock the `MongoDataBackend.read` method always raising an Exception."""
        yield {"_source": {}}
        raise BackendException(msg)

    backend = mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            list(backend.query_statements_by_ids(RalphStatementsQuery.model_construct()))

    assert (
        "ralph.backends.lrs.mongo",
        logging.ERROR,
        "Failed to read from MongoDB",
    ) in caplog.record_tuples
    backend.close()


def test_backends_lrs_mongo_lrs_backend_query_statements_by_ids_with_two_collections(
    mongo, mongo_forwarding, mongo_lrs_backend
):
    """Test the `MongoLRSBackend.query_statements_by_ids` method, given a valid search
    query, should execute the query only on the specified collection and return the
    expected results.
    """
    # pylint: disable=unused-argument

    # Instantiate Mongo Databases
    backend_1 = mongo_lrs_backend()
    backend_2 = mongo_lrs_backend(default_collection=MONGO_TEST_FORWARDING_COLLECTION)

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    assert backend_1.write([{"id": "1", **timestamp}]) == 1
    assert backend_2.write([{"id": "2", **timestamp}]) == 1

    # Check the expected search query results
    assert list(backend_1.query_statements_by_ids(["1"])) == [{"id": "1", **timestamp}]
    assert not list(backend_1.query_statements_by_ids(["2"]))
    assert not list(backend_2.query_statements_by_ids(["1"]))
    assert list(backend_2.query_statements_by_ids(["2"])) == [{"id": "2", **timestamp}]
    backend_1.close()
    backend_2.close()
