"""Tests for the POST statements endpoint of the Ralph API"""

import re
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ralph.api import app
from ralph.exceptions import BackendException

from tests.fixtures.backends import get_es_test_backend, get_mongo_test_backend

client = TestClient(app)


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_api_statements_post_single_statement_directly(
    backend, monkeypatch, auth_credentials, es, mongo
):
    """Tests the post statements API route with one statement."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
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
        "timestamp": "2022-06-22T08:31:38Z",
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

    response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statement]}


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_api_statements_post_statements_list_of_one(
    backend, monkeypatch, auth_credentials, es, mongo
):
    """Tests the post statements API route with one statement in a list."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
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
        "timestamp": "2022-03-15T14:07:51Z",
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

    response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statement]}


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_api_statements_post_statements_list(
    backend, monkeypatch, auth_credentials, es, mongo
):
    """Tests the post statements API route with two statements in a list."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
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
            "timestamp": "2022-03-15T14:07:52Z",
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
            "timestamp": "2022-03-15T14:07:51Z",
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
    generated_id = response.json()[1]
    assert regex.match(generated_id)
    es.indices.refresh()

    get_response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )
    assert get_response.status_code == 200
    # Update statements with the generated id.
    statements[1] = statements[1] | {"id": generated_id}
    assert get_response.json() == {"statements": statements}


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_api_statements_post_statements_list_with_duplicates(
    backend, monkeypatch, auth_credentials, es_data_stream, mongo
):
    """Tests the post statements API route with duplicate statement IDs should fail."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
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
        "timestamp": "2022-03-15T14:07:51Z",
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
    # The failure should imply no statement insertion.
    es_data_stream.indices.refresh()
    response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )
    assert response.status_code == 200
    assert response.json() == {"statements": []}


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_api_statements_post_statements_list_with_duplicate_of_existing_statement(
    backend, monkeypatch, auth_credentials, es, mongo
):
    """Tests the post statements API route, given a statement that already exist in the
    database (has the same ID), should fail.
    """
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
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
        "timestamp": "2022-03-15T14:07:51Z",
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    # Post the statement once.
    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 200

    es.indices.refresh()

    # Post the statement twice, trying to change the version field which is not allowed.
    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=[statement | {"version": "1.0.0"}],
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Statements already exist with the same ID"}

    response = client.get(
        "/xAPI/statements/", headers={"Authorization": f"Basic {auth_credentials}"}
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statement]}


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_api_statements_post_statements_with_a_failure_during_storage(
    backend, monkeypatch, auth_credentials, es, mongo
):
    """Tests the post statements API route with a failure happening during storage."""
    # pylint: disable=invalid-name,unused-argument, too-many-arguments

    def put_mock(*args, **kwargs):
        """Raises an exception. Mocks the database.put method."""

        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(backend_instance, "put", put_mock)
    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT", backend_instance
    )
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
        "timestamp": "2022-03-15T14:07:51Z",
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Statements bulk indexation failed"}


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_api_statements_post_statements_with_a_failure_during_id_query(
    backend, monkeypatch, auth_credentials, es, mongo
):
    """Tests the post statements API route with a failure during query execution."""
    # pylint: disable=invalid-name,unused-argument, too-many-arguments

    def query_statements_by_ids_mock(*args, **kwargs):
        """Raises an exception. Mocks the database.query_statements_by_ids method."""

        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(
        backend_instance, "query_statements_by_ids", query_statements_by_ids_mock
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT", backend_instance
    )
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
        "timestamp": "2022-03-15T14:07:51Z",
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    response = client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}
