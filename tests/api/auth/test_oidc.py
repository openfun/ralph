"""Tests for the api.auth.oidc module."""
import pytest
import responses
from fastapi.testclient import TestClient
from pydantic import parse_obj_as

from ralph.api import app
from ralph.api.auth.oidc import discover_provider, get_public_keys
from ralph.conf import AuthBackend
from ralph.models.xapi.base.agents import BaseXapiAgentWithOpenId

from tests.fixtures.auth import ISSUER_URI, mock_oidc_user
from tests.helpers import configure_env_for_mock_oidc_auth

client = TestClient(app)


@pytest.mark.parametrize(
    "runserver_auth_backends",
    [[AuthBackend.BASIC, AuthBackend.OIDC], [AuthBackend.OIDC]],
)
@responses.activate
def test_api_auth_oidc_valid(monkeypatch, runserver_auth_backends):
    """Test a valid OpenId Connect authentication."""

    configure_env_for_mock_oidc_auth(monkeypatch, runserver_auth_backends)

    oidc_token = mock_oidc_user(scopes=["all", "profile/read"])

    headers = {"Authorization": f"Bearer {oidc_token}"}
    response = client.get(
        "/whoami",
        headers=headers,
    )
    assert response.status_code == 200
    assert len(response.json().keys()) == 2
    assert response.json()["agent"] == {"openid": "https://iss.example.com/123|oidc"}
    assert parse_obj_as(BaseXapiAgentWithOpenId, response.json()["agent"])
    assert sorted(response.json()["scopes"]) == ["all", "profile/read"]


@responses.activate
def test_api_auth_invalid_token(monkeypatch, mock_discovery_response, mock_oidc_jwks):
    """Test API with an invalid audience."""

    configure_env_for_mock_oidc_auth(monkeypatch)

    mock_oidc_user()

    response = client.get(
        "/whoami",
        headers={"Authorization": "Bearer wrong_token"},
    )

    assert response.status_code == 401
    # assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Invalid authentication credentials"}


@responses.activate
def test_api_auth_invalid_discovery(monkeypatch, encoded_token):
    """Test API with an invalid provider discovery."""

    configure_env_for_mock_oidc_auth(monkeypatch)

    # Clear LRU cache
    discover_provider.cache_clear()
    get_public_keys.cache_clear()

    # Mock request to get provider configuration
    responses.add(
        responses.GET,
        f"{ISSUER_URI}/.well-known/openid-configuration",
        json=None,
        status=500,
    )

    response = client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {encoded_token}"},
    )

    assert response.status_code == 401
    # assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Invalid authentication credentials"}


@responses.activate
def test_api_auth_invalid_keys(
    monkeypatch, mock_discovery_response, mock_oidc_jwks, encoded_token
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

    response = client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {encoded_token}"},
    )

    assert response.status_code == 401
    # assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Invalid authentication credentials"}


@responses.activate
def test_api_auth_invalid_header(monkeypatch):
    """Test API with an invalid request header."""

    configure_env_for_mock_oidc_auth(monkeypatch)

    oidc_token = mock_oidc_user()

    response = client.get(
        "/whoami",
        headers={"Authorization": f"Wrong header {oidc_token}"},
    )

    assert response.status_code == 401
    # assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Invalid authentication credentials"}
