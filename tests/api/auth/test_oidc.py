"""Tests for the api.auth.oidc module."""

import responses

from ralph.api.auth.oidc import discover_provider, get_public_keys

from tests.fixtures.auth import ISSUER_URI


@responses.activate
def test_api_auth_oidc_valid(
    oidc_auth_test_client, mock_discovery_response, mock_oidc_jwks, encoded_token
):
    """Test a valid OpenId Connect authentication."""

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
        status=200,
    )

    response = oidc_auth_test_client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {encoded_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "scopes": ["all", "statements/read"],
        "agent": {"openid": "123|oidc"},
    }


@responses.activate
def test_api_auth_invalid_token(
    oidc_auth_test_client, mock_discovery_response, mock_oidc_jwks
):
    """Test API with an invalid audience."""

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
        status=200,
    )

    response = oidc_auth_test_client.get(
        "/whoami",
        headers={"Authorization": "Bearer wrong_token"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}


@responses.activate
def test_api_auth_invalid_discovery(oidc_auth_test_client, encoded_token):
    """Test API with an invalid provider discovery."""

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

    response = oidc_auth_test_client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {encoded_token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}


@responses.activate
def test_api_auth_invalid_keys(
    oidc_auth_test_client, mock_discovery_response, mock_oidc_jwks, encoded_token
):
    """Test API with an invalid request for keys."""

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

    response = oidc_auth_test_client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {encoded_token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}


@responses.activate
def test_api_auth_invalid_header(
    oidc_auth_test_client, mock_discovery_response, mock_oidc_jwks, encoded_token
):
    """Test API with an invalid request header."""

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
        status=200,
    )

    response = oidc_auth_test_client.get(
        "/whoami",
        headers={"Authorization": f"Wrong header {encoded_token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}
