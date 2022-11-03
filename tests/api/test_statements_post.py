"""Tests for the POST statements endpoint of the Ralph API."""

import re
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ralph.api import app
from ralph.backends.database.es import ESDatabase
from ralph.backends.database.mongo import MongoDatabase
from ralph.conf import XapiForwardingConfigurationSettings
from ralph.exceptions import BackendException

from tests.fixtures.backends import (
    ES_TEST_FORWARDING_INDEX,
    ES_TEST_HOSTS,
    MONGO_TEST_CONNECTION_URI,
    MONGO_TEST_DATABASE,
    MONGO_TEST_FORWARDING_COLLECTION,
    RUNSERVER_TEST_HOST,
    RUNSERVER_TEST_PORT,
    get_es_test_backend,
    get_mongo_test_backend,
)

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
    # pylint: disable=invalid-name,unused-argument,too-many-arguments

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


@pytest.mark.parametrize("backend", [get_es_test_backend, get_mongo_test_backend])
def test_post_statements_list_without_statement_forwarding(
    backend, auth_credentials, monkeypatch, es, mongo
):
    """Tests the post statements API route, given an empty forwarding configuration,
    should not start the forwarding background task.
    """
    # pylint: disable=invalid-name,unused-argument

    spy = {}

    def spy_mock_forward_xapi_statements(_):
        """Mocks the forward_xapi_statements; spies over whether it has been called."""

        spy["error"] = "forward_xapi_statements should not have been called!"

    monkeypatch.setattr(
        "ralph.api.routers.statements.forward_xapi_statements",
        spy_mock_forward_xapi_statements,
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.get_active_xapi_forwardings", lambda: []
    )
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
    assert "error" not in spy


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "receiving_backend", [get_es_test_backend, get_mongo_test_backend]
)
@pytest.mark.parametrize(
    "forwarding_backend",
    [
        lambda: ESDatabase(hosts=ES_TEST_HOSTS, index=ES_TEST_FORWARDING_INDEX),
        lambda: MongoDatabase(
            connection_uri=MONGO_TEST_CONNECTION_URI,
            database=MONGO_TEST_DATABASE,
            collection=MONGO_TEST_FORWARDING_COLLECTION,
        ),
    ],
)
async def test_post_statements_list_with_statement_forwarding(
    receiving_backend,
    forwarding_backend,
    monkeypatch,
    auth_credentials,
    es,
    es_forwarding,
    mongo,
    mongo_forwarding,
    lrs,
):
    """Tests the xAPI forwarding functionality given two ralph instances - a forwarding
    instance and a receiving instance. When the forwarding instance receives a valid
    xAPI statement it should store and forward it to the receiving instance which in
    turn should store it too.
    """
    # pylint: disable=invalid-name,unused-argument,too-many-arguments,too-many-locals

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

    # Set-up receiving LRS client
    with monkeypatch.context() as receiving_patch:
        # Receiving client should not forward statements
        receiving_patch.setattr(
            "ralph.api.forwarding.get_active_xapi_forwardings", lambda: []
        )
        # Receiving client should use the receiving Elasticsearch client for storage
        receiving_patch.setattr(
            "ralph.api.routers.statements.DATABASE_CLIENT", receiving_backend()
        )
        lrs_context = lrs(app)
        # Start receiving LRS client
        await lrs_context.__aenter__()  # pylint: disable=unnecessary-dunder-call

    # Set-up forwarding client.
    with monkeypatch.context() as forwarding_patch:
        # Forwarding client should forward statements to receiving client.
        url = f"http://{RUNSERVER_TEST_HOST}:{RUNSERVER_TEST_PORT}/xAPI/statements/"
        forwarding_patch.setattr(
            "ralph.api.forwarding.get_active_xapi_forwardings",
            lambda: [
                XapiForwardingConfigurationSettings(
                    url=url,
                    is_active=True,
                    basic_username="ralph",
                    basic_password="admin",
                    max_retries=1,
                    timeout=10,
                )
            ],
        )
        # Forwarding client should use the forwarding Elasticsearch client for storage
        forwarding_patch.setattr(
            "ralph.api.routers.statements.DATABASE_CLIENT", forwarding_backend()
        )
        # Start forwarding LRS client
        async with AsyncClient(
            app=app, base_url="http://testserver"
        ) as forwarding_client:
            # Send an xAPI statement to the forwarding client
            response = await forwarding_client.post(
                "/xAPI/statements/",
                auth=("ralph", "admin"),
                json=statement,
            )
            assert response.status_code == 200

            es.indices.refresh()
            es_forwarding.indices.refresh()

            # The statement should be stored on the forwarding client
            response = await forwarding_client.get(
                "/xAPI/statements/",
                headers={"Authorization": f"Basic {auth_credentials}"},
            )
            assert response.status_code == 200
            assert response.json() == {"statements": [statement]}

    # The statement should also be stored on the receiving client
    async with AsyncClient() as receiving_client:
        response = await receiving_client.get(
            f"http://{RUNSERVER_TEST_HOST}:{RUNSERVER_TEST_PORT}/xAPI/statements/",
            headers={"Authorization": f"Basic {auth_credentials}"},
        )
        assert response.status_code == 200
        assert response.json() == {"statements": [statement]}

    # Stop receiving LRS client
    lrs_context.__aexit__(None, None, None)
