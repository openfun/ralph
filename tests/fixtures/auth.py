"""Test fixtures related to authentication on the API."""
import base64
import json
import os
from typing import Optional

import bcrypt
import pytest
import responses
from cryptography.hazmat.primitives import serialization
from jose import jwt
from jose.utils import long_to_base64

from ralph.api.auth.basic import get_stored_credentials
from ralph.api.auth.oidc import discover_provider, get_public_keys
from ralph.conf import settings

from . import private_key, public_key

ALGORITHM = "RS256"
AUDIENCE = "http://clientHost:8100"
ISSUER_URI = "http://providerHost:8080/auth/realms/real_name"
PUBLIC_KEY_ID = "example-key-id"


def mock_basic_auth_user(
    fs_,
    username: str = "jane",
    password: str = "pwd",
    scopes: Optional[list] = None,
    agent: Optional[dict] = None,
):
    """Create a user using Basic Auth in the (fake) file system.

    Args:
        fs_: fixture provided by pyfakefs
        username (str): username used for auth
        password (str): password used for auth
        scopes (List[str]): list of scopes available to the user
        agent (dict): an agent that represents the user and may be used as authority
    """

    # Default values for `scopes` and `agent`
    if scopes is None:
        scopes = []
    if agent is None:
        agent = {"mbox": "mailto:jane@ralphlrs.com"}

    # Basic HTTP auth
    credential_bytes = base64.b64encode(f"{username}:{password}".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.AUTH_FILE  # settings.APP_DIR / "auth.json"

    # Clear lru_cache to allow for basic auth testing within same function
    get_stored_credentials.cache_clear()

    all_users = []
    if os.path.exists(auth_file_path):
        with open(auth_file_path, encoding="utf-8") as file:
            all_users = json.loads(file.read())
        os.remove(auth_file_path)

    user = {
        "username": username,
        "hash": bcrypt.hashpw(bytes(password.encode("utf-8")), bcrypt.gensalt()).decode(
            "UTF-8"
        ),
        "scopes": scopes,
        "agent": agent,
    }
    all_users.append(user)

    fs_.create_file(auth_file_path, contents=json.dumps(all_users))

    return credentials


@pytest.fixture
def basic_auth_credentials(fs, user_scopes=None, agent=None):
    """Set up the credentials file for request authentication.

    Args:
        fs: fixture provided by pyfakefs (not called in the code)
        user_scopes (List[str]): list of scopes to associate to the user
        agent (dict): valid Agent (per xAPI specification) representing the user

    Returns:
        credentials (str): auth parameters that need to be passed
            through headers to authenticate the request.
    """

    username = "ralph"
    password = "admin"
    if user_scopes is None:
        user_scopes = ["all"]
    if agent is None:
        agent = {"mbox": "mailto:test_ralph@example.com"}

    credentials = mock_basic_auth_user(fs, username, password, user_scopes, agent)
    return credentials


def _mock_discovery_response():
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


@pytest.fixture
def mock_discovery_response():
    """Return an example discovery response (fixture)."""
    return _mock_discovery_response()


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


def _mock_oidc_jwks():
    """Mock OpenID Connect keys."""
    return {"keys": [get_jwk(public_key)]}


@pytest.fixture
def mock_oidc_jwks():
    """Mock OpenID Connect keys (fixture)."""
    return _mock_oidc_jwks()


def _create_oidc_token(sub, scopes):
    """Encode token with the private key."""
    return jwt.encode(
        claims={
            "sub": sub,
            "iss": "https://iss.example.com",
            "aud": AUDIENCE,
            "iat": 0,  # Issued the 1/1/1970
            "exp": 9999999999,  # Expiring in 11/20/2286
            "scope": " ".join(scopes),
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


def mock_oidc_user(sub="123|oidc", scopes=None):
    """Instantiate mock oidc user and return auth token."""
    # Default value for scope
    if scopes is None:
        scopes = ["all", "statements/read"]

    # Clear LRU cache
    discover_provider.cache_clear()
    get_public_keys.cache_clear()

    # Mock request to get provider configuration
    responses.add(
        responses.GET,
        f"{ISSUER_URI}/.well-known/openid-configuration",
        json=_mock_discovery_response(),
        status=200,
    )

    # Mock request to get keys
    responses.add(
        responses.GET,
        _mock_discovery_response()["jwks_uri"],
        json=_mock_oidc_jwks(),
        status=200,
    )

    oidc_token = _create_oidc_token(sub=sub, scopes=scopes)
    return oidc_token


@pytest.fixture
def encoded_token():
    """Encode token with the private key (fixture)."""
    return _create_oidc_token(sub="123|oidc", scopes=["all", "statements/read"])
