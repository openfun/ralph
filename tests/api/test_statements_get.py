"""Tests for the GET statements endpoint of the Ralph API."""

import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import pytest
from elasticsearch.helpers import bulk
from fastapi.testclient import TestClient

from ralph.api import app
from ralph.backends.database.clickhouse import ClickHouseDatabase
from ralph.backends.database.mongo import MongoDatabase
from ralph.exceptions import BackendException

from tests.fixtures.backends import (
    CLICKHOUSE_TEST_DATABASE,
    CLICKHOUSE_TEST_HOST,
    CLICKHOUSE_TEST_PORT,
    CLICKHOUSE_TEST_TABLE_NAME,
    ES_TEST_INDEX,
    MONGO_TEST_COLLECTION,
    MONGO_TEST_DATABASE,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)

client = TestClient(app)


def insert_es_statements(es_client, statements):
    """Inserts a bunch of example statements into Elasticsearch for testing."""
    bulk(
        es_client,
        [
            {
                "_index": ES_TEST_INDEX,
                "_id": statement["id"],
                "_op_type": "index",
                "_source": statement,
            }
            for statement in statements
        ],
    )
    es_client.indices.refresh()


def insert_mongo_statements(mongo_client, statements):
    """Inserts a bunch of example statements into MongoDB for testing."""
    database = getattr(mongo_client, MONGO_TEST_DATABASE)
    collection = getattr(database, MONGO_TEST_COLLECTION)
    collection.insert_many(list(MongoDatabase.to_documents(statements)))


def insert_clickhouse_statements(statements):
    """Inserts a bunch of example statements into ClickHouse for testing."""
    backend = ClickHouseDatabase(
        host=CLICKHOUSE_TEST_HOST,
        port=CLICKHOUSE_TEST_PORT,
        database=CLICKHOUSE_TEST_DATABASE,
        event_table_name=CLICKHOUSE_TEST_TABLE_NAME,
    )
    # documents = list(ClickHouseDatabase.to_documents(statements))
    success = backend.put(statements)
    assert success == len(statements)


@pytest.fixture(params=["es", "mongo", "clickhouse"])
# pylint: disable=unused-argument
def insert_statements_and_monkeypatch_backend(
    request, es, mongo, clickhouse, monkeypatch
):
    """Retuns a function that inserts statements into each backend."""
    # pylint: disable=invalid-name

    def _insert_statements_and_monkeypatch_backend(statements):
        """Inserts statements once into each backend."""
        database_client_class_path = "ralph.api.routers.statements.DATABASE_CLIENT"
        if request.param == "mongo":
            insert_mongo_statements(mongo, statements)
            monkeypatch.setattr(database_client_class_path, get_mongo_test_backend())
            return
        if request.param == "clickhouse":
            insert_clickhouse_statements(statements)
            monkeypatch.setattr(
                database_client_class_path, get_clickhouse_test_backend()
            )
            return
        insert_es_statements(es, statements)
        monkeypatch.setattr(database_client_class_path, get_es_test_backend())

    return _insert_statements_and_monkeypatch_backend


def test_api_statements_get_statements(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route without any filters set up."""
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}


def test_api_statements_get_statements_ascending(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given an "ascending" query parameter, should
    return statements in ascending order by their timestamp.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?ascending=true",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0], statements[1]]}


def test_api_statements_get_statements_by_statement_id(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given a "statementId" query parameter, should
    return a list of statements matching the given statementId.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        f"/xAPI/statements/?statementId={statements[1]['id']}",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_api_statements_get_statements_by_agent(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given an "agent" query parameter, should
    return a list of statements filtered by the given agent.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "actor": {"account": {"name": "96d61e6c-9cdb-4926-9cff-d3a15c662999"}},
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "actor": {"account": {"name": "cdcb1c95-dd5b-4085-8236-9c1580051155"}},
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?agent=96d61e6c-9cdb-4926-9cff-d3a15c662999",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


def test_api_statements_get_statements_by_verb(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given a "verb" query parameter, should
    return a list of statements filtered by the given verb id.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/experienced"},
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/played"},
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?verb=" + quote_plus("http://adlnet.gov/expapi/verbs/played"),
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_api_statements_get_statements_by_activity(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given an "activity" query parameter, should
    return a list of statements filtered by the given activity id.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "object": {
                "id": "58d8bede-155f-48b1-b1ff-a41eb28c2f0b",
                "objectType": "Activity",
            },
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "object": {
                "id": "a2956991-200b-40a7-9548-293cdcc06c4b",
                "objectType": "Activity",
            },
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?activity=a2956991-200b-40a7-9548-293cdcc06c4b",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_api_statements_get_statements_since_timestamp(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given a "since" query parameter, should
    return a list of statements filtered by the given timestamp.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    since = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = client.get(
        f"/xAPI/statements/?since={since}",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


def test_api_statements_get_statements_until_timestamp(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given an "until" query parameter,
    should return a list of statements filtered by the given timestamp.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    until = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = client.get(
        f"/xAPI/statements/?until={until}",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


def test_api_statements_get_statements_with_pagination(
    monkeypatch, insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given a request leading to more results than
    can fit on the first page, should return a list of statements non exceeding the page
    limit and include a "more" property with a link to get the next page of results.
    """
    # pylint: disable=redefined-outer-name

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.RUNSERVER_MAX_SEARCH_HITS_COUNT", 2
    )

    statements = [
        {
            "id": "5d345b99-517c-4b54-848e-45010904b177",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )
    assert first_response.status_code == 200
    assert first_response.json()["statements"] == [statements[2], statements[1]]
    more_regex = re.compile(r"^/xAPI/statements/\?pit_id=.*&search_after=.*$")
    assert more_regex.match(first_response.json()["more"])

    # Second response gets the missing result from the first response.
    second_response = client.get(
        first_response.json()["more"],
        headers={"Authorization": f"Basic {auth_credentials}"},
    )
    assert second_response.status_code == 200
    assert second_response.json() == {"statements": [statements[0]]}


def test_api_statements_get_statements_with_no_matching_statement(
    insert_statements_and_monkeypatch_backend, auth_credentials
):
    """Tests the get statements API route, given a query yielding no matching statement,
    should return an empty list.
    """
    # pylint: disable=redefined-outer-name

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = client.get(
        "/xAPI/statements/?statementId=66c81e98-1763-4730-8cfc-f5ab34f1bad5",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": []}


def test_api_statements_get_statements_with_database_query_failure(
    auth_credentials, monkeypatch
):
    """Tests the get statements API route, given a query raising a BackendException,
    should return an error response with HTTP code 500.
    """
    # pylint: disable=redefined-outer-name

    def mock_query_statements(*_):
        """Mocks the DATABASE_CLIENT.query_statements method."""
        raise BackendException()

    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT.query_statements",
        mock_query_statements,
    )

    response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}
