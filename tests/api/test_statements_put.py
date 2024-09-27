"""Tests for the PUT statements endpoint of the Ralph API."""

from uuid import uuid4

import pytest
import responses
from httpx import AsyncClient

from ralph.api import app
from ralph.api.auth.basic import get_basic_auth_user
from ralph.backends.lrs.es import ESLRSBackend
from ralph.backends.lrs.mongo import MongoLRSBackend
from ralph.conf import AuthBackend, XapiForwardingConfigurationSettings
from ralph.exceptions import BackendException

from tests.fixtures.auth import (
    AUDIENCE,
    ISSUER_URI,
    mock_basic_auth_user,
    mock_oidc_user,
)
from tests.fixtures.backends import (
    ES_TEST_FORWARDING_INDEX,
    ES_TEST_HOSTS,
    MONGO_TEST_CONNECTION_URI,
    MONGO_TEST_DATABASE,
    MONGO_TEST_FORWARDING_COLLECTION,
    RUNSERVER_TEST_HOST,
    RUNSERVER_TEST_PORT,
    get_async_es_test_backend,
    get_async_mongo_test_backend,
    get_clickhouse_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)

from ..helpers import (
    assert_statement_get_responses_are_equivalent,
    mock_agent,
    mock_statement,
    string_is_date,
)


@pytest.mark.anyio
async def test_api_statements_put_invalid_parameters(client, basic_auth_credentials):
    """Test that using invalid parameters returns the proper status code."""
    statement = mock_statement()

    # Check for 400 status code when unknown parameters are provided
    response = await client.put(
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
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
@pytest.mark.anyio
async def test_api_statements_put_single_statement_directly(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route with one statement."""

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 204

    es.indices.refresh()

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
@pytest.mark.anyio
async def test_api_statements_put_single_statement_to_target(  # noqa: PLR0913
    fs,
    client,
    backend,
    monkeypatch,
    basic_auth_credentials,
    es_custom,
    mongo_custom,
    clickhouse_custom,
):
    """Test the put statements API route with one statement to a custom target."""

    # Create one user with a specific target
    username = "jane"
    password = "janepwd"
    scopes = []
    target = "custom_target"
    agent = mock_agent("account", 1, home_page_id=1)

    credentials = mock_basic_auth_user(fs, username, password, scopes, agent, target)

    # Clear cache before each test iteration
    get_basic_auth_user.cache_clear()

    # Create custom target
    es_client = es_custom(index=target)
    mongo_custom(collection=target)
    clickhouse_custom(event_table_name=target)

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {credentials}"},
        json=statement,
    )

    assert response.status_code == 204

    es_client.indices.refresh()

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {credentials}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.anyio
async def test_api_statements_put_enriching_without_existing_values(
    client, monkeypatch, basic_auth_credentials, es
):
    """Test that statements are properly enriched when statement provides no values."""

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT", get_es_test_backend()
    )
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 204

    es.indices.refresh()

    response = await client.get(
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
    assert statement["authority"] == {
        "mbox": "mailto:test_ralph@example.com",
        "objectType": "Agent",
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "field,value,status",
    [
        ("timestamp", "2022-06-22T08:31:38Z", 204),
        ("stored", "2022-06-22T08:31:38Z", 204),
        (
            "authority",
            {"mbox": "mailto:test_ralph@example.com", "objectType": "Agent"},
            204,
        ),
    ],
)
async def test_api_statements_put_enriching_with_existing_values(  # noqa: PLR0913
    client, field, value, status, monkeypatch, basic_auth_credentials, es
):
    """Test that statements are properly enriched when values are provided."""

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT", get_es_test_backend()
    )
    statement = mock_statement()

    # Add the field to be tested
    statement[field] = value

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == status

    # Check that values match when they should
    if status == 204:
        es.indices.refresh()
        response = await client.get(
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


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_statements_put_single_statement_no_trailing_slash(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test that the statements endpoint also works without the trailing slash."""

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 204


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_statements_put_id_mismatch(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route when the statementId doesn't match."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement(id_=str(uuid4()))

    different_statement_id = str(uuid4())
    response = await client.put(
        f"/xAPI/statements/?statementId={different_statement_id}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "xAPI statement id does not match given statementId"
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_statements_put_list_of_one(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test that we fail on PUTs with a list, even if it's one statement."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=[statement],
    )

    assert response.status_code == 400


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_statements_put_duplicate_of_existing_statement(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route, given a statement that already exist in the
    database (has the same ID), should fail.
    """

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    # Put the statement once.
    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 204

    es.indices.refresh()

    # Put the statement twice, trying to change the timestamp, which is not allowed
    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=dict(statement, **{"timestamp": "2023-03-15T14:07:51Z"}),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A different statement already exists with the same ID"
    }

    response = await client.get(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_statements_put_with_failure_during_storage(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route with a failure happening during storage."""

    def write_mock(*args, **kwargs):
        """Raise an exception. Mocks the database.write method."""
        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(backend_instance, "write", write_mock)
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend_instance)
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Statement indexation failed"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_statements_put_with_a_failure_during_id_query(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the put statements API route with a failure during query execution."""

    def query_statements_by_ids_mock(*args, **kwargs):
        """Raise an exception. Mock the database.query_statements_by_ids method."""
        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(
        backend_instance, "query_statements_by_ids", query_statements_by_ids_mock
    )
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend_instance)
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_statements_put_without_forwarding(  # noqa: PLR0913
    client, backend, basic_auth_credentials, monkeypatch, es, mongo, clickhouse
):
    """Test the put statements API route, given an empty forwarding configuration,
    should not start the forwarding background task.
    """

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
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())

    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 204


@pytest.mark.anyio
@pytest.mark.parametrize(
    "receiving_backend",
    [
        get_es_test_backend,
        get_mongo_test_backend,
    ],
)
@pytest.mark.parametrize(
    "forwarding_backend",
    [
        lambda: ESLRSBackend(
            settings=ESLRSBackend.settings_class(
                HOSTS=ES_TEST_HOSTS, DEFAULT_INDEX=ES_TEST_FORWARDING_INDEX
            )
        ),
        lambda: MongoLRSBackend(
            settings=MongoLRSBackend.settings_class(
                CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
                DEFAULT_DATABASE=MONGO_TEST_DATABASE,
                DEFAULT_COLLECTION=MONGO_TEST_FORWARDING_COLLECTION,
            )
        ),
    ],
)
async def test_api_statements_put_with_forwarding(  # noqa: PLR0913
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

    statement = mock_statement()

    # Set-up receiving LRS client
    with monkeypatch.context() as receiving_patch:
        # Receiving client should not forward statements
        receiving_patch.setattr(
            "ralph.api.forwarding.get_active_xapi_forwardings", lambda: []
        )
        # Receiving client should use the receiving Elasticsearch client for storage
        receiving_patch.setattr(
            "ralph.api.routers.statements.BACKEND_CLIENT", receiving_backend()
        )
        lrs_context = lrs(app)
        # Start receiving LRS client
        await lrs_context.__aenter__()

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
            "ralph.api.routers.statements.BACKEND_CLIENT", forwarding_backend()
        )
        # Start forwarding LRS client
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"X-Experience-API-Version": "1.0.3"},
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
    async with AsyncClient(
        headers={"X-Experience-API-Version": "1.0.3"}
    ) as receiving_client:
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


@pytest.mark.anyio
@responses.activate
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
async def test_api_statements_put_scopes(  # noqa: PLR0913
    client, monkeypatch, fs, es, auth_method, scopes, is_authorized
):
    """Test that putting statements behaves properly according to user scopes."""

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr("ralph.api.auth.basic.settings.LRS_RESTRICT_BY_SCOPES", True)

    if auth_method == "basic":
        agent = mock_agent("mbox", 1)
        credentials = mock_basic_auth_user(fs, scopes=scopes, agent=agent)
        headers = {"Authorization": f"Basic {credentials}"}

        get_basic_auth_user.cache_clear()

    elif auth_method == "oidc":
        sub = "123|oidc"
        agent = {"openid": sub}
        oidc_token = mock_oidc_user(sub=sub, scopes=scopes)
        headers = {"Authorization": f"Bearer {oidc_token}"}

        monkeypatch.setenv("RUNSERVER_AUTH_BACKENDS", "oidc")
        monkeypatch.setattr(
            "ralph.api.auth.settings.RUNSERVER_AUTH_BACKENDS", [AuthBackend.OIDC]
        )
        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_ISSUER_URI",
            ISSUER_URI,
        )
        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_AUDIENCE",
            AUDIENCE,
        )

    statement = mock_statement()

    # NB: scopes are not linked to statements and backends, we therefore test with ES
    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    monkeypatch.setattr(backend_client_class_path, get_es_test_backend())

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers=headers,
        json=statement,
    )

    if is_authorized:
        assert response.status_code == 204
    else:
        assert response.status_code == 401
        assert response.json() == {
            "detail": 'Access not authorized to scope: "statements/write".'
        }
