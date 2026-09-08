"""Tests for the api.auth.oidc module."""

import pytest
import responses
from pydantic import TypeAdapter
from fastapi import HTTPException
import json

from ralph.api.auth.oidc import (
    discover_provider,
    get_public_keys,
    get_token_introspection,
    get_user_info_data,
    get_user_info,
    UserInfo,
    TokenIntrospection,
)
from ralph.models.xapi.base.agents import BaseXapiAgentWithOpenId
from ralph.conf import AuthBackend

from tests.fixtures.auth import ISSUER_URI, TOKEN_ISS, OTHER_CLIENT_ID, mock_oidc_user, encode_jwt
from tests.fixtures.backends import get_es_test_backend
from tests.helpers import (
    assert_statement_get_responses_are_equivalent,
    configure_env_for_mock_oidc_auth,
    mock_statement,
)

@pytest.mark.anyio
@pytest.mark.parametrize(
    "response_content_type,is_valid,token_data",
    [
        ("application/json", True, {"sub": "my_user_2", "scope": "statements/write"}),
        ("application/jwt", True, {"sub": "my_user_1", "scope": "statements/write"}),
    ],
)
@responses.activate
async def test_api_auth_oidc_userinfo(
    mock_discovery_response,
    mock_oidc_jwks,
    response_content_type,
    is_valid,
    token_data,
):

    user_info = UserInfo(**token_data)
    auth_header = "Bearer a_token"

    # Cache clear
    get_user_info_data.cache_clear()

    response_body = token_data
    if response_content_type == "application/json":
        response_body = json.dumps(token_data)
    elif response_content_type == "application/jwt":
        responses.add(
            responses.GET,
            mock_discovery_response["jwks_uri"],
            json=mock_oidc_jwks,
            status=200,
            headers={"Content-Type": "application/json"},
        )
        algorithms = mock_discovery_response["id_token_signing_alg_values_supported"]
        response_body = encode_jwt(algorithm=algorithms[0], claims=token_data)
    responses.add(
        responses.GET,
        mock_discovery_response["userinfo_endpoint"],
        body=response_body,
        status=200,
        headers={"Content-Type": response_content_type},
    )

    if is_valid:
        res_user_info = get_user_info(mock_discovery_response, auth_header=auth_header)

        assert res_user_info == user_info
    else:
        with pytest.raises(HTTPException) as exc_info:
            get_user_info(mock_discovery_response, auth_header=auth_header)
        assert exc_info.value.status_code == 400
        assert "text/html" in exc_info.value.detail


@pytest.mark.anyio
@pytest.mark.parametrize(
    "active,access_token,token_data",
    [
        (
            True,
            "a_token",
            {
                "iss": TOKEN_ISS,
                "client_id": "client_1",
                "sub": "my_user_1",
                "scope": "statements/write",
                "exp": 3600,
                "iat": 0,
            },
        ),
        (
            True,
            "another_token",
            {
                "iss": TOKEN_ISS,
                "client_id": "client_2",
                "scope": "statements/write",
                "exp": 3600,
                "iat": 0,
            },
        ),
        (
            False,
            "an_invalid_token",
            {
                "iss": TOKEN_ISS,
                "client_id": "client_1",
                "sub": "my_user_2",
                "scope": "statements/write",
                "exp": 3600,
                "iat": 0,
            },
        ),
    ],
)
@responses.activate
async def test_api_auth_oidc_introspection(
    mock_discovery_response, active, access_token, token_data
):

    client_basic_auth_header = "Basic aaaaa"

    # Cache clear
    get_user_info_data.cache_clear()

    response_body = {**token_data, "active": active}

    responses.add(
        responses.POST,
        mock_discovery_response["introspection_endpoint"],
        json=response_body,
        status=200,
        headers={"Content-Type": "application/json"},
    )
    if active:
        token_info = TokenIntrospection(**token_data)
        res_token_info = get_token_introspection(
            mock_discovery_response["introspection_endpoint"],
            token=access_token,
            client_basic_auth_header=client_basic_auth_header,
        )
        assert res_token_info == token_info
    else:
        with pytest.raises(HTTPException) as exc_info:
            get_token_introspection(
                mock_discovery_response["introspection_endpoint"],
                token=access_token,
                client_basic_auth_header=client_basic_auth_header,
            )
            assert exc_info.value.status_code == 401


@pytest.mark.anyio
@responses.activate
@pytest.mark.parametrize(
    "runserver_auth_backends,sub,enable_oidc_client,userinfo_response_type",
    [
        ([AuthBackend.BASIC, AuthBackend.OIDC], "user_1", True, "jwt"),
        ([AuthBackend.OIDC], "user_2", True, "plain"),
        ([AuthBackend.OIDC], "user_3", True, "jwt"),
        ([AuthBackend.OIDC], None, True, "jwt"),
        ([AuthBackend.OIDC], "user_4", False, None),
    ],
)
async def test_api_auth_oidc_get_whoami_valid(
    client,
    monkeypatch,
    runserver_auth_backends,
    sub,
    enable_oidc_client,
    userinfo_response_type,
):
    """Test a valid OpenId Connect authentication."""

    configure_env_for_mock_oidc_auth(
        monkeypatch, runserver_auth_backends, enable_oidc_client=enable_oidc_client
    )

    oidc_token = mock_oidc_user(
        sub=sub,
        scopes=["all", "profile/read"],
        userinfo_response_type=userinfo_response_type,
    )

    headers = {"Authorization": f"Bearer {oidc_token}"}
    response = await client.get(
        "/whoami",
        headers=headers,
    )
    assert response.status_code == 200
    assert len(response.json().keys()) == 2
    agent = {
        "openid": (
            f"{TOKEN_ISS}/application/{OTHER_CLIENT_ID}"
            if sub is None
            else f"{TOKEN_ISS}/{sub}"
        ),
        "objectType": "Agent",
    }

    assert response.json()["agent"] == agent
    assert TypeAdapter(BaseXapiAgentWithOpenId).validate_python(
        response.json()["agent"]
    )
    assert sorted(response.json()["scopes"]) == ["all", "profile/read"]
    assert "target" not in response.json()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "runserver_auth_backends,userinfo_response_type",
    [
        ([AuthBackend.BASIC, AuthBackend.OIDC], "jwt"),
        ([AuthBackend.OIDC], "plain"),
        ([AuthBackend.OIDC], "jwt"),
    ],
)
@responses.activate
async def test_api_auth_oidc_post_statements_to_target(
    client, monkeypatch, runserver_auth_backends, es_custom, userinfo_response_type
):
    """Test a valid OpenId Connect authentication."""

    configure_env_for_mock_oidc_auth(monkeypatch, runserver_auth_backends)

    # Create user pointing to a custom target
    target = "custom_target"
    oidc_token = mock_oidc_user(
        scopes=["all", "profile/read"],
        target=target,
        userinfo_response_type=userinfo_response_type,
    )

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT", get_es_test_backend()
    )
    statement = mock_statement()

    # Create both default and custom indexes
    es_custom()
    es_client = es_custom(index=target)

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Bearer {oidc_token}"},
        json=statement,
    )
    assert response.status_code == 200

    es_client.indices.refresh(index=target)

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Bearer {oidc_token}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )

    # Check that a user with default target cannot see these statements
    oidc_token = mock_oidc_user(scopes=["all", "profile/read"])

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Bearer {oidc_token}"},
    )
    assert response.status_code == 500


@pytest.mark.anyio
@pytest.mark.parametrize(
    "userinfo_response_type",
    ["jwt", "plain"],
)
@responses.activate
async def test_api_auth_oidc_get_whoami_invalid_token(
    client, monkeypatch, userinfo_response_type
):
    """Test API with an invalid audience."""

    configure_env_for_mock_oidc_auth(monkeypatch)

    mock_oidc_user(userinfo_response_type=userinfo_response_type)

    response = await client.get(
        "/whoami",
        headers={"Authorization": "Bearer wrong_token"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.anyio
@responses.activate
async def test_api_auth_oidc_get_whoami_invalid_discovery(
    client, monkeypatch, access_token
):
    """Test API with an invalid provider discovery."""

    configure_env_for_mock_oidc_auth(monkeypatch)

    # Clear LRU cache
    discover_provider.cache_clear()
    get_public_keys.cache_clear()
    get_token_introspection.cache_clear()
    get_user_info_data.cache_clear()

    # Mock request to get provider configuration
    responses.add(
        responses.GET,
        f"{ISSUER_URI}/.well-known/openid-configuration",
        json=None,
        status=500,
    )

    response = await client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.anyio
@responses.activate
async def test_api_auth_oidc_get_whoami_invalid_keys(
    client, monkeypatch, mock_discovery_response, mock_oidc_jwks, access_token
):
    """Test API with an invalid request for keys."""

    configure_env_for_mock_oidc_auth(monkeypatch)

    # Clear LRU cache
    discover_provider.cache_clear()
    get_public_keys.cache_clear()

    # Mock request to get provider configuration
    responses.add(
        responses.GET,
        f"{ISSUER_URI}/.well-known/openid-configuration",
        json=mock_discovery_response,
        status=200,
    )

    # Mock request to get keys
    responses.add(
        responses.GET,
        mock_discovery_response["jwks_uri"],
        json=mock_oidc_jwks,
        status=500,
    )

    response = await client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.anyio
@responses.activate
async def test_api_auth_oidc_get_whoami_invalid_header(client, monkeypatch):
    """Test API with an invalid request header."""

    configure_env_for_mock_oidc_auth(monkeypatch)

    oidc_token = mock_oidc_user()

    response = await client.get(
        "/whoami",
        headers={"Authorization": f"Wrong header {oidc_token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.anyio
@responses.activate
async def test_api_auth_oidc_get_whoami_invalid_backend(client, fs, monkeypatch):
    """Check for an exception when providing valid OIDC credentials while
    OIDC authentication is not supported.
    """

    configure_env_for_mock_oidc_auth(monkeypatch, [AuthBackend.BASIC])

    oidc_token = mock_oidc_user(scopes=["all", "profile/read"])

    headers = {"Authorization": f"Bearer {oidc_token}"}
    response = await client.get(
        "/whoami",
        headers=headers,
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}
