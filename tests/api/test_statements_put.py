"""Tests for the PUT statements endpoint of the Ralph API."""
from importlib import reload
from uuid import uuid4

import pytest
import responses
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ralph import api
from ralph.api import app
from ralph.api.auth import get_authenticated_user
from ralph.api.auth.basic import get_authenticated_user as get_basic_user
from ralph.api.auth.oidc import get_authenticated_user as get_oidc_user
from ralph.backends.database.es import ESDatabase
from ralph.backends.database.mongo import MongoDatabase
from ralph.conf import XapiForwardingConfigurationSettings
from ralph.exceptions import BackendException

from tests.fixtures.auth import create_mock_basic_auth_user, create_mock_oidc_user
from tests.fixtures.backends import (
    ES_TEST_FORWARDING_INDEX,
    ES_TEST_HOSTS,
    MONGO_TEST_CONNECTION_URI,
    MONGO_TEST_DATABASE,
    MONGO_TEST_FORWARDING_COLLECTION,
    RUNSERVER_TEST_HOST,
    RUNSERVER_TEST_PORT,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)

from ..helpers import (
    assert_statement_get_responses_are_equivalent,
    create_mock_agent,
    mock_statement,
    string_is_date,
)

reload(api)
client = TestClient(app)


def test_api_statements_put_invalid_parameters(basic_auth_credentials):
    """Test that using invalid parameters returns the proper status code."""
    statement = mock_statement()

    # Check for 400 status code when unknown parameters are provided
    response = client.put(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "The following parameter is not allowed: `mamamia`"
    }


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
# pylint: disable=too-many-arguments
def test_api_statements_put_single_statement_directly(
    backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route with one statement."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
    statement = mock_statement()

    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 204

    es.indices.refresh()

    response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


# pylint: disable=too-many-arguments
def test_api_statements_put_enriching_without_existing_values(
    monkeypatch, basic_auth_credentials, es
):
    """Test that statements are properly enriched when statement provides no values."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT", get_es_test_backend()
    )
    statement = {
        "actor": {
            "account": {
                "homePage": "https://example.com/homepage/",
                "name": str(uuid4()),
            },
            "objectType": "Agent",
        },
        "object": {"id": "https://example.com/object-id/1/"},
        "verb": {"id": "https://example.com/verb-id/1/"},
        "id": str(uuid4()),
    }

    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 204

    es.indices.refresh()

    response = client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    statement = response.json()["statements"][0]

    # Test pre-processing: id
    assert "id" in statement
    assert statement

    # Test pre-processing: timestamp
    assert "timestamp" in statement
    assert string_is_date(statement["timestamp"])

    # Test pre-processing: stored
    assert "stored" in statement
    assert string_is_date(statement["stored"])

    # Test pre-processing: authority
    assert "authority" in statement
    assert statement["authority"] == {"mbox": "mailto:test_ralph@example.com"}


@pytest.mark.parametrize(
    "field,value,status",
    [
        ("timestamp", "2022-06-22T08:31:38Z", 204),
        ("stored", "2022-06-22T08:31:38Z", 204),
        ("authority", {"mbox": "mailto:test_ralph@example.com"}, 204),
    ],
)
# pylint: disable=too-many-arguments
def test_api_statements_put_enriching_with_existing_values(
    field, value, status, monkeypatch, basic_auth_credentials, es
):
    """Test that statements are properly enriched when values are provided."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT", get_es_test_backend()
    )
    statement = mock_statement()
    # Add the field to be tested
    statement[field] = value

    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == status

    # Check that values match when they should
    if status == 204:
        es.indices.refresh()
        response = client.get(
            "/xAPI/statements/",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        statement = response.json()["statements"][0]

        # Test enriching
        assert field in statement
        if field == "stored":
            # Check that stored value was overwritten
            assert statement[field] != value
        else:
            assert statement[field] == value


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
# pylint: disable=too-many-arguments
def test_api_statements_put_single_statement_no_trailing_slash(
    backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test that the statements endpoint also works without the trailing slash."""
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
    statement = mock_statement()

    response = client.put(
        f"/xAPI/statements?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 204


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
# pylint: disable=too-many-arguments
def test_api_statements_put_statement_id_mismatch(
    backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    # pylint: disable=invalid-name,unused-argument
    """Test the put statements API route when the statementId doesn't match."""
    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
    statement = mock_statement(id_=str(uuid4()))

    different_statement_id = str(uuid4())
    response = client.put(
        f"/xAPI/statements/?statementId={different_statement_id}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "xAPI statement id does not match given statementId"
    }


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
# pylint: disable=too-many-arguments
def test_api_statements_put_list_of_one(
    backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    # pylint: disable=invalid-name,unused-argument
    """Test that we fail on PUTs with a list, even if it's one statement."""
    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
    statement = mock_statement()

    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=[statement],
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
# pylint: disable=too-many-arguments
def test_api_statements_put_statement_duplicate_of_existing_statement(
    backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route, given a statement that already exist in the
    database (has the same ID), should fail.
    """
    # pylint: disable=invalid-name,unused-argument

    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())
    statement = mock_statement()

    # Put the statement once.
    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 204

    es.indices.refresh()

    # Put the statement twice, trying to change the timestamp, which is not allowed
    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=dict(statement, **{"timestamp": "2023-03-15T14:07:51Z"}),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A different statement already exists with the same ID"
    }

    response = client.get(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
def test_api_statement_put_statements_with_a_failure_during_storage(
    backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route with a failure happening during storage."""
    # pylint: disable=invalid-name,unused-argument, too-many-arguments

    def put_mock(*args, **kwargs):
        """Raise an exception. Mock the database.put method."""
        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(backend_instance, "put", put_mock)
    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT", backend_instance
    )
    statement = mock_statement()

    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Statement indexation failed"}


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
def test_api_statements_put_statement_with_a_failure_during_id_query(
    backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route with a failure during query execution."""
    # pylint: disable=invalid-name,unused-argument,too-many-arguments

    def query_statements_by_ids_mock(*args, **kwargs):
        """Raise an exception. Mock the database.query_statements_by_ids method."""
        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(
        backend_instance, "query_statements_by_ids", query_statements_by_ids_mock
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.DATABASE_CLIENT", backend_instance
    )
    statement = mock_statement()

    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.parametrize(
    "backend",
    [get_es_test_backend, get_clickhouse_test_backend, get_mongo_test_backend],
)
# pylint: disable=too-many-arguments
def test_put_statement_without_statement_forwarding(
    backend, basic_auth_credentials, monkeypatch, es, mongo, clickhouse
):
    """Test the put statements API route, given an empty forwarding configuration,
    should not start the forwarding background task.
    """
    # pylint: disable=invalid-name,unused-argument

    spy = {}

    def spy_mock_forward_xapi_statements(_):
        """Mock the forward_xapi_statements; spies over whether it has been called."""
        spy["error"] = "forward_xapi_statements should not have been called!"

    monkeypatch.setattr(
        "ralph.api.routers.statements.forward_xapi_statements",
        spy_mock_forward_xapi_statements,
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.get_active_xapi_forwardings", lambda: []
    )
    monkeypatch.setattr("ralph.api.routers.statements.DATABASE_CLIENT", backend())

    statement = mock_statement()

    response = client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 204


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
async def test_put_statement_with_statement_forwarding(
    receiving_backend,
    forwarding_backend,
    monkeypatch,
    basic_auth_credentials,
    es,
    es_forwarding,
    mongo,
    mongo_forwarding,
    lrs,
):
    """Test the xAPI forwarding functionality given two ralph instances - a forwarding
    instance and a receiving instance. When the forwarding instance receives a valid
    xAPI statement it should store and forward it to the receiving instance which in
    turn should store it too.
    """
    # pylint: disable=invalid-name,unused-argument,too-many-arguments,too-many-locals

    statement = mock_statement()

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
        url = (
            f"http://{RUNSERVER_TEST_HOST}:"
            f"{RUNSERVER_TEST_PORT}/xAPI/statements/?statementId={statement['id']}"
        )
        forwarding_config = XapiForwardingConfigurationSettings(
            url=url,
            is_active=True,
            basic_username="ralph",
            basic_password="admin",
            max_retries=1,
            timeout=10,
        )
        forwarding_patch.setattr(
            "ralph.api.forwarding.get_active_xapi_forwardings",
            lambda: [forwarding_config],
        )
        # Trigger addition of background tasks
        forwarding_patch.setattr(
            "ralph.api.routers.statements.get_active_xapi_forwardings",
            lambda: [forwarding_config],
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
            response = await forwarding_client.put(
                f"/xAPI/statements/?statementId={statement['id']}",
                auth=("ralph", "admin"),
                json=statement,
            )
            assert response.status_code == 204

            es.indices.refresh()
            es_forwarding.indices.refresh()

            # The statement should be stored on the forwarding client
            response = await forwarding_client.get(
                "/xAPI/statements/",
                headers={"Authorization": f"Basic {basic_auth_credentials}"},
            )
            assert response.status_code == 200
            assert_statement_get_responses_are_equivalent(
                response.json(), {"statements": [statement]}
            )

    # The statement should also be stored on the receiving client
    async with AsyncClient() as receiving_client:
        response = await receiving_client.get(
            f"http://{RUNSERVER_TEST_HOST}:{RUNSERVER_TEST_PORT}/xAPI/statements/",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code == 200
        assert_statement_get_responses_are_equivalent(
            response.json(), {"statements": [statement]}
        )

    # Stop receiving LRS client
    await lrs_context.__aexit__(None, None, None)


@responses.activate()
@pytest.mark.parametrize("auth_method", ["basic", "oidc"])
@pytest.mark.parametrize(
    "scopes,is_authorized",
    [
        (["all"], True),
        (["profile/read", "statements/write"], True),
        (["all/read"], False),
        (["statements/read/mine"], False),
        (["profile/write"], False),
        ([], False),
    ],
)
def test_api_statements_put_scopes(
    monkeypatch, fs, es, auth_method, scopes, is_authorized
):
    """Test that getting statements behaves properly according to user scopes."""
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr("ralph.api.auth.basic.settings.LRS_RESTRICT_BY_SCOPES", True)

    if auth_method == "basic":
        agent = create_mock_agent("mbox", 1)
        username = "jane"
        password = "janepwd"
        credentials = create_mock_basic_auth_user(fs, username, password, scopes, agent)
        headers = {"Authorization": f"Basic {credentials}"}

        app.dependency_overrides[get_authenticated_user] = get_basic_user
        get_basic_user.cache_clear()

    elif auth_method == "oidc":
        sub = "123|oidc"
        agent = {"openid": sub}
        oidc_token = create_mock_oidc_user(sub=sub, scopes=scopes)
        headers = {"Authorization": f"Bearer {oidc_token}"}

        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_ISSUER_URI",
            "http://providerHost:8080/auth/realms/real_name",
        )
        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_AUDIENCE",
            "http://clientHost:8100",
        )

        app.dependency_overrides[get_authenticated_user] = get_oidc_user

    statement = mock_statement()

    # NB: scopes are not linked to statements and backends, we therefore test with ES
    database_client_class_path = "ralph.api.routers.statements.DATABASE_CLIENT"
    monkeypatch.setattr(database_client_class_path, get_es_test_backend())

    response = client.post(
        "/xAPI/statements/",
        headers=headers,
        json=statement,
    )

    if is_authorized:
        assert response.status_code == 200
    else:
        assert response.status_code == 401
        assert response.json() == {
            "detail": 'Access not authorized to scope: "statements/write".'
        }

    app.dependency_overrides.pop(get_authenticated_user, None)
