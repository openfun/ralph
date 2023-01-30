"""Test fixtures related to authentication on the API."""
import base64
import json
from importlib import reload

import bcrypt
import pytest
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient
from jose import jwt
from jose.utils import long_to_base64

from ralph import api, conf
from ralph.conf import settings

from . import private_key, public_key

ALGORITHM = "RS256"
AUDIENCE = "http://clientHost:8100"
ISSUER_URI = "http://providerHost:8080/auth/realms/real_name"
PUBLIC_KEY_ID = "example-key-id"


# pylint: disable=invalid-name
@pytest.fixture
def auth_credentials(fs):
    """Sets up the credentials file for request authentication.

    Returns:
        credentials (str): auth parameters that need to be passed
            through headers to authenticate the request.
    """
    credential_bytes = base64.b64encode("ralph:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(
        auth_file_path,
        contents=json.dumps(
            [
                {
                    "username": "ralph",
                    "hash": bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("UTF-8"),
                    "scopes": ["ralph_test_scope"],
                }
            ]
        ),
    )

    return credentials


@pytest.fixture
def basic_auth_test_client(monkeypatch):
    """Return a TestClient with HTTP basic authentication mode."""
    monkeypatch.setenv("RALPH_RUNSERVER_AUTH_BACKEND", "basic")
    monkeypatch.setenv("RALPH_RUNSERVER_AUTH_OIDC_ISSUER_URI", ISSUER_URI)
    monkeypatch.setenv("RALPH_RUNSERVER_AUTH_OIDC_AUDIENCE", AUDIENCE)
    reload(conf)
    reload(api.auth)
    app = reload(api).app
    yield TestClient(app)


@pytest.fixture
def oidc_auth_test_client(monkeypatch):
    """Return a TestClient with OpenId Connect authentication mode."""
    monkeypatch.setenv("RALPH_RUNSERVER_AUTH_BACKEND", "oidc")
    monkeypatch.setenv("RALPH_RUNSERVER_AUTH_OIDC_ISSUER_URI", ISSUER_URI)
    monkeypatch.setenv("RALPH_RUNSERVER_AUTH_OIDC_AUDIENCE", AUDIENCE)
    reload(conf)
    reload(api.auth.oidc)
    reload(api.auth)
    app = reload(api).app
    yield TestClient(app)


@pytest.fixture
def mock_discovery_response():
    """Return an example discovery response."""
    return {
        "issuer": "http://providerHost",
        "authorization_endpoint": "https://providerHost:8080/auth/oauth/v2/authorize",
        "token_endpoint": "https://providerHost:8080/auth/oauth/v2/token",
        "jwks_uri": "https://providerHost:8080/openid/connect/jwks.json",
        "response_types_supported": [
            "code",
            "token id_token",
            "token",
            "code id_token",
            "id_token",
            "code token",
            "code token id_token",
        ],
        "subject_types_supported": [
            "pairwise",
        ],
        "id_token_signing_alg_values_supported": [
            "RS256",
            "HS256",
        ],
        "userinfo_endpoint": "https://providerHost:8080/openid/connect/v1/userinfo",
        "registration_endpoint": "https://providerHost:8080/openid/connect/register",
        "scopes_supported": [
            "openid",
            "email",
            "profile",
            "oidc_test_client_registration",
        ],
        "claims_supported": [
            "iss",
            "ver",
            "sub",
            "aud",
            "iat",
            "exp",
            "jti",
            "auth_time",
            "amr",
            "idp",
            "nonce",
            "name",
            "nickname",
            "preferred_username",
            "given_name",
            "middle_name",
            "family_name",
            "email",
            "email_verified",
            "profile",
            "zoneinfo",
            "locale",
            "address",
            "phone_number",
            "picture",
            "website",
            "gender",
            "birthdate",
            "updated_at",
            "at_hash",
            "c_hash",
        ],
        "grant_types_supported": [
            "authorization_code",
            "implicit",
            "refresh_token",
            "password",
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
            "client_secret_jwt",
            "private_key_jwt",
        ],
        "claim_types_supported": ["normal"],
        "response_modes_supported": [
            "query",
            "fragment",
            "form_post",
        ],
        "userinfo_signing_alg_values_supported": [
            "RS256",
            "HS256",
        ],
    }


def get_jwk(pub_key):
    """Return a JWK representation of the public key."""
    public_numbers = pub_key.public_numbers()

    return {
        "kid": PUBLIC_KEY_ID,
        "alg": ALGORITHM,
        "kty": "RSA",
        "use": "sig",
        "n": long_to_base64(public_numbers.n).decode("ASCII"),
        "e": long_to_base64(public_numbers.e).decode("ASCII"),
    }


@pytest.fixture
def mock_oidc_jwks():
    """Mock OpenID Connect keys."""
    return {"keys": [get_jwk(public_key)]}


@pytest.fixture
def encoded_token():
    """Encode token with the private key."""
    return jwt.encode(
        claims={
            "sub": "123|oidc",
            "iss": "some-issuer",
            "aud": AUDIENCE,
            "iat": 0,  # Issued the 1/1/1970
            "exp": 9999999999,  # Expiring in 11/20/2286
        },
        key=private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
        algorithm=ALGORITHM,
        headers={
            "kid": PUBLIC_KEY_ID,
        },
    )
