"""Tests for the POST statements endpoint of the Ralph API."""

import re
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
    string_is_uuid,
)


@pytest.mark.anyio
async def test_api_statements_post_invalid_parameters(client, basic_auth_credentials):
    """Test that using invalid parameters returns the proper status code."""

    statement = mock_statement()

    # Check for 400 status code when unknown parameters are provided
    response = await client.post(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "The following parameter is not allowed: `mamamia`"
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
async def test_api_statements_post_single_statement_directly(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the post statements API route with one statement."""

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]

    es.indices.refresh()

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.anyio
async def test_api_statements_post_enriching_without_existing_values(
    client, monkeypatch, basic_auth_credentials, es
):
    """Test that statements are properly enriched when statement provides no values."""

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT", get_es_test_backend()
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
    }

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 200

    es.indices.refresh()

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    statement = response.json()["statements"][0]

    # Test pre-processing: id
    assert "id" in statement
    assert string_is_uuid(statement["id"])

    # Test pre-processing: timestamp
    assert "timestamp" in statement
    assert string_is_date(statement["timestamp"])

    # Test pre-processing: stored
    assert "stored" in statement
    assert string_is_date(statement["stored"])

    # Test pre-processing: authority
    assert "authority" in statement
    assert statement["authority"] == {"mbox": "mailto:test_ralph@example.com"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "field,value,status",
    [
        ("id", str(uuid4()), 200),
        ("timestamp", "2022-06-22T08:31:38Z", 200),
        ("stored", "2022-06-22T08:31:38Z", 200),
        ("authority", {"mbox": "mailto:test_ralph@example.com"}, 200),
    ],
)
async def test_api_statements_post_enriching_with_existing_values(  # noqa: PLR0913
    client, field, value, status, monkeypatch, basic_auth_credentials, es
):
    """Test that statements are properly enriched when values are provided."""

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT", get_es_test_backend()
    )
    statement = mock_statement()

    # Add the field to be tested
    statement[field] = value

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == status

    # Check that values match when they should
    if status == 200:
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
async def test_api_statements_post_single_statement_no_trailing_slash(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test that the statements endpoint also works without the trailing slash."""

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]


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
async def test_api_statements_post_list_of_one(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the post statements API route with one statement in a list."""

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=[statement],
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]
    es.indices.refresh()

    response = await client.get(
        "/xAPI/statements/",
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
async def test_api_statements_post_list(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the post statements API route with two statements in a list."""

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())

    statement_1 = mock_statement(timestamp="2022-03-15T14:07:52Z")

    # Note the second statement has no preexisting ID
    statement_2 = mock_statement(timestamp="2022-03-15T14:07:51Z")
    statement_2.pop("id")

    statements = [statement_1, statement_2]

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statements,
    )

    assert response.status_code == 200
    assert response.json()[0] == statements[0]["id"]
    regex = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    generated_id = response.json()[1]
    assert regex.match(generated_id)
    es.indices.refresh()

    get_response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert get_response.status_code == 200

    # Update statements with the generated id.
    statements[1] = dict(statements[1], **{"id": generated_id})

    assert_statement_get_responses_are_equivalent(
        get_response.json(), {"statements": statements}
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
async def test_api_statements_post_list_with_duplicates(  # noqa: PLR0913
    client,
    backend,
    monkeypatch,
    basic_auth_credentials,
    es_data_stream,
    mongo,
    clickhouse,
):
    """Test the post statements API route with duplicate statement IDs should fail."""

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=[statement, statement],
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Duplicate statement IDs in the list of statements"
    }
    # The failure should imply no statement insertion.
    es_data_stream.indices.refresh()
    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": []}


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
async def test_api_statements_post_list_with_duplicate_of_existing_statement(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the post statements API route, given a statement that already exist in the
    database (has the same ID), should fail.
    """

    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())

    statement_uuid = str(uuid4())
    statement = mock_statement(id_=statement_uuid)

    # Post the statement once.
    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 200
    assert response.json() == [statement_uuid]

    es.indices.refresh()

    # Post the statement twice, the data is identical so it should succeed but not
    # include the ID in the response as it wasn't inserted.
    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )
    assert response.status_code == 204

    es.indices.refresh()

    # Post the statement again, trying to change the timestamp which is not allowed.
    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=[dict(statement, **{"timestamp": "2023-03-15T14:07:51Z"})],
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": f"Differing statements already exist with the same ID: "
        f"{statement_uuid}"
    }

    response = await client.get(
        "/xAPI/statements/",
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
async def test_api_statements_post_with_failure_during_storage(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the post statements API route with a failure happening during storage."""

    async def write_mock(*args, **kwargs):
        """Raise an exception. Mocks the database.write method."""
        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(backend_instance, "write", write_mock)
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend_instance)
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Statements bulk indexation failed"}


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
async def test_api_statements_post_with_failure_during_id_query(  # noqa: PLR0913
    client, backend, monkeypatch, basic_auth_credentials, es, mongo, clickhouse
):
    """Test the post statements API route with a failure during query execution."""

    def query_statements_by_ids_mock(*args, **kwargs):
        """Raise an exception. Mock the database.query_statements_by_ids method."""
        raise BackendException()

    backend_instance = backend()
    monkeypatch.setattr(
        backend_instance, "query_statements_by_ids", query_statements_by_ids_mock
    )
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend_instance)
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
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
async def test_api_statements_post_list_without_forwarding(  # noqa: PLR0913
    client, backend, basic_auth_credentials, monkeypatch, es, mongo, clickhouse
):
    """Test the post statements API route, given an empty forwarding configuration,
    should not start the forwarding background task.
    """

    spy = {}

    async def spy_mock_forward_xapi_statements(_):
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

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
        json=statement,
    )

    assert response.status_code == 200
    assert "error" not in spy


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
async def test_api_statements_post_list_with_forwarding(  # noqa: PLR0913
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
        # Receiving client should use the receiving backend for storage
        receiving_patch.setattr(
            "ralph.api.routers.statements.BACKEND_CLIENT", receiving_backend()
        )

        lrs_context = lrs(app)
        # Start receiving LRS client
        await lrs_context.__aenter__()

    # Set-up forwarding client.
    with monkeypatch.context() as forwarding_patch:
        # Forwarding client should forward statements to receiving client.
        url = f"http://{RUNSERVER_TEST_HOST}:{RUNSERVER_TEST_PORT}/xAPI/statements/"
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
async def test_api_statements_post_scopes(  # noqa: PLR0913
    client, monkeypatch, fs, es, auth_method, scopes, is_authorized
):
    """Test that posting statements behaves properly according to user scopes."""

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

    response = await client.post(
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
