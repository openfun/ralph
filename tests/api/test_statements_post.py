"""
Tests for the POST statements endpoint of the Ralph API.
"""
import re
from unittest import mock
from uuid import uuid4

from fastapi.testclient import TestClient

from ralph.api import app
from ralph.backends.database.es import ESDatabase

from tests.fixtures.backends import ES_TEST_INDEX

client = TestClient(app)


# pylint: disable=invalid-name
@mock.patch("ralph.api.routers.statements.ES_CLIENT", ESDatabase(index=ES_TEST_INDEX))
def test_post_single_statement_directly(auth_credentials, es):
    """
    Statements POST supports adding one statement by passing it as a JSON dict.
    """

    statement = {
        "actor": {
            "account": {
                "homePage": "https://example.com/homepage/",
                "name": str(uuid4()),
            },
            "objectType": "Agent",
        },
        "id": str(uuid4()),
        "object": {"id": "https://example.com/object-id/1/"},
        "timestamp": 1647349671,
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]
    es.indices.refresh()
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 1
    assert hits[0]["_id"] == statement["id"]


# pylint: disable=invalid-name
@mock.patch("ralph.api.routers.statements.ES_CLIENT", ESDatabase(index=ES_TEST_INDEX))
def test_post_statements_list_of_one(auth_credentials, es):
    """
    Statements POST supports adding one statement by just
    passing a list of one statement.
    """

    statement = {
        "actor": {
            "account": {
                "homePage": "https://example.com/homepage/",
                "name": str(uuid4()),
            },
            "objectType": "Agent",
        },
        "id": str(uuid4()),
        "object": {"id": "https://example.com/object-id/1/"},
        "timestamp": 1647349671,
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=[statement],
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]
    es.indices.refresh()
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 1
    assert hits[0]["_id"] == statement["id"]


# pylint: disable=invalid-name
@mock.patch("ralph.api.routers.statements.ES_CLIENT", ESDatabase(index=ES_TEST_INDEX))
def test_post_statements_list(auth_credentials, es):
    """
    Statements POST supports adding more than one statement by just
    passing a list of statements.
    """

    statements = [
        {
            "actor": {
                "account": {
                    "homePage": "https://example.com/homepage/",
                    "name": str(uuid4()),
                },
                "objectType": "Agent",
            },
            "id": str(uuid4()),
            "object": {"id": "https://example.com/object-id/1/"},
            "timestamp": 1647349671,
            "verb": {"id": "https://example.com/verb-id/1/"},
        },
        {
            "actor": {
                "account": {
                    "homePage": "https://example.com/homepage/",
                    "name": str(uuid4()),
                },
                "objectType": "Agent",
            },
            # Note the second statement has no preexisting ID
            "object": {"id": "https://example.com/object-id/1/"},
            "timestamp": 1647349671,
            "verb": {"id": "https://example.com/verb-id/1/"},
        },
    ]

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=statements,
    )

    assert response.status_code == 200
    assert response.json()[0] == statements[0]["id"]
    regex = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    assert regex.match(response.json()[1])
    es.indices.refresh()
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 2
    assert hits[0]["_id"] == statements[0]["id"]
    assert hits[1]["_id"] == response.json()[1]


# pylint: disable=invalid-name
def test_post_statements_list_with_duplicates(auth_credentials, es):
    """
    A POST statements request with duplicate statement IDs should fail.
    """

    statement = {
        "actor": {
            "account": {
                "homePage": "https://example.com/homepage/",
                "name": str(uuid4()),
            },
            "objectType": "Agent",
        },
        "id": str(uuid4()),
        "object": {"id": "https://example.com/object-id/1/"},
        "timestamp": 1647349671,
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=[statement, statement],
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Duplicate statement IDs in the list of statements"
    }
    es.indices.refresh()
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 0


# pylint: disable=invalid-name
@mock.patch("ralph.api.routers.statements.ES_CLIENT", ESDatabase(index=ES_TEST_INDEX))
def test_post_statements_list_with_duplicate_of_existing_statement(
    auth_credentials, es
):
    """
    A POST statements request containing a statement with an ID that already
    exists in the database should fail.
    """

    statement = {
        "actor": {
            "account": {
                "homePage": "https://example.com/homepage/",
                "name": str(uuid4()),
            },
            "objectType": "Agent",
        },
        "id": str(uuid4()),
        "object": {"id": "https://example.com/object-id/1/"},
        "timestamp": 1647349671,
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
    es.index(
        index=ES_TEST_INDEX,
        id=statement["id"],
        document=statement,
    )
    es.indices.refresh()

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=[statement],
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Statements already exist with the same ID"}
    es.indices.refresh()
    hits = es.search(index=ES_TEST_INDEX)["hits"]["hits"]
    assert len(hits) == 1
