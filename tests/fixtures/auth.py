"""Test fixtures related to authentication on the API."""

import base64
import json
import os
import urllib.parse
from typing import Callable, Literal, Optional, Union

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
TOKEN_ISS = "https://iss.example.com"
CLIENT_ID = "my-client-id"
OTHER_CLIENT_ID = "my-other-client-id"
CLIENT_SECRET = "my-client-secret"
PUBLIC_KEY_ID = "example-key-id"


def mock_basic_auth_user(  # noqa: PLR0913
    fs_,
    username: str = "jane",
    password: str = "pwd",
    scopes: Optional[list] = None,
    agent: Optional[dict] = None,
    target: Optional[str] = None,
):
    """Create a user using Basic Auth in the (fake) file system.

    Args:
        fs_: fixture provided by pyfakefs
        username (str): username used for auth
        password (str): password used for auth
        scopes (List[str]): list of scopes available to the user
        agent (dict): an agent that represents the user and may be used as authority
        target (str): The target index or database to store statements into.
    """

    # Default values for `scopes` and `agent`
    if scopes is None:
        scopes = []
    if agent is None:
        agent = {"mbox": "mailto:jane@ralphlrs.com"}

    # Basic HTTP auth
    credential_bytes = base64.b64encode(f"{username}:{password}".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.AUTH_FILE

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
    if target is not None:
        user["target"] = target
    all_users.append(user)

    fs_.create_file(auth_file_path, contents=json.dumps(all_users))

    return credentials


@pytest.fixture
def basic_auth_credentials(fs, user_scopes=None, agent=None, target=None):
    """Set up the credentials file for request authentication.

    Args:
        fs: fixture provided by pyfakefs (not called in the code)
        user_scopes (List[str]): list of scopes to associate to the user
        agent (dict): valid Agent (per xAPI specification) representing the user
        target (str): The target index or database to store statements into.

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

    credentials = mock_basic_auth_user(
        fs, username, password, user_scopes, agent, target
    )
    return credentials


def _mock_discovery_response():
    """Return an example discovery response."""
    return {
        "issuer": "http://providerHost",
        "authorization_endpoint": "https://providerHost:8080/auth/oauth/v2/authorize",
        "token_endpoint": "https://providerHost:8080/auth/oauth/v2/token",
        "jwks_uri": "https://providerHost:8080/openid/connect/jwks.json",
        "introspection_endpoint": "https://providerHost:8080/auth/oauth/v2/introspect",
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


def encode_jwt(
    claims, algorithm: str = "HS256", headers: dict = None, access_token: str = None
):
    return jwt.encode(
        access_token=access_token,
        algorithm=algorithm,
        key=private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
        headers=headers,
        claims=claims,
    )


def _mock_oidc_jwks():
    """Mock OpenID Connect keys."""
    return {"keys": [get_jwk(public_key)]}


@pytest.fixture
def mock_oidc_jwks():
    """Mock OpenID Connect keys (fixture)."""
    return _mock_oidc_jwks()


def _mock_access_token(sub, scopes, target=None):
    return base64.urlsafe_b64encode(
        f"opaque_string_{sub}_{scopes}_{target}".encode()
    ).decode()


def _mock_oidc_introspection_response(sub, scopes, target=None):
    """Mock OIDC Token Introspection response with provided params."""
    token_introspection = {
        "iss": TOKEN_ISS,
        "aud": AUDIENCE,
        "iat": 0,  # Issued the 1/1/1970
        "exp": 9999999999,  # Expiring in 11/20/2286
        "scope": " ".join(scopes),
        "active": True,
        "client_id": OTHER_CLIENT_ID,
        "token_type": "Bearer",
    }
    if sub is not None:
        token_introspection["sub"] = sub
    if target is not None:
        token_introspection["target"] = target
    return token_introspection


def _mock_oidc_user_info_plain_response(sub: str, scopes, target=None):
    """Mock unencoded OIDC user info claims with provided params."""
    if sub is None:
        raise ValueError(
            "The IdP `/userinfo` endpoint cannot return `UserInfo` without a `sub` claim."
        )
    user_info = {
        "sub": sub,
        "scope": " ".join(scopes),
    }
    if target is not None:
        user_info["target"] = target
    return user_info


def protect_oidc_client_basic_callback(
    result: Union[dict, Callable[[dict], tuple]], client_id: str, client_secret: str
):
    def _callback(request):
        auth_header = request.headers["Authorization"]
        auth_method = auth_header.split(" ")[0]
        if auth_method.lower() != "basic":
            return (401, {}, "")
        client_secret_basic_token = auth_header.split(" ")[-1]
        decoded_client_secret_basic_token = base64.b64decode(
            client_secret_basic_token.encode("utf-8")
        ).decode("utf-8")
        id = decoded_client_secret_basic_token.split(":")[0]
        secret = decoded_client_secret_basic_token.split(":")[1]
        if id != client_id or secret != client_secret:
            return (401, {}, "")
        if isinstance(result, Callable):
            return result(request)
        return (
            200,
            {"Content-Type": "application/json"},
            json.dumps(result),
        )

    return _callback


def protect_oidc_token_callback(
    result: Union[dict, Callable[[dict], tuple]], access_token: str
):
    def _callback(request):
        auth_header = request.headers["Authorization"]
        auth_method = auth_header.split(" ")[0]
        if auth_method.lower() != "bearer":
            return (401, {}, "")
        token = auth_header.split(" ")[-1]
        if token != access_token:
            return (401, {}, "")
        if isinstance(result, Callable):
            return result(request)
        return (
            200,
            {"Content-Type": "application/json"},
            json.dumps(result),
        )

    return _callback


def mock_oidc_user(
    sub: Union[str, None] = "123|oidc",
    scopes=None,
    target=None,
    userinfo_response_type: Union[Literal["plain", "jwt"], None] = "jwt",
):
    """Instantiate mock oidc user and return auth token.

    If `userinfo_response_type` is None, produces an OIDC Id token in the JWT format,
    from which the `UserInfo` can be decoded without another request to IdP.
    Otherwise, creates an opaque access token.
    If `sub` is None, the access token can be inspected with
    the IdP's `/introspection`.
    If `sub` is not None, the access token can be traded for`UserInfo` using
    the IdP's `/introspection` and `/userinfo` endpoints.
    """
    # Default value for scope
    if scopes is None:
        scopes = ["all", "statements/read"]

    if sub is None and userinfo_response_type is None:
        raise ValueError(
            "Cannot return a Client Credentials access token"
            "if not using the IdP's `/introspection` and `/userinfo` endpoints"
        )

    # Clear LRU cache
    discover_provider.cache_clear()
    get_public_keys.cache_clear()

    provider_config = _mock_discovery_response()
    # Mock request to get provider configuration
    responses.add(
        responses.GET,
        f"{ISSUER_URI}/.well-known/openid-configuration",
        json=provider_config,
        status=200,
    )

    # Mock request to get keys
    responses.add(
        responses.GET,
        provider_config["jwks_uri"],
        json=_mock_oidc_jwks(),
        status=200,
    )

    if userinfo_response_type is None:
        user_info = _mock_oidc_user_info_plain_response(
            sub=sub, scopes=scopes, target=target
        )
        oidc_jwt_token = encode_jwt(
            claims={**user_info, "iss": TOKEN_ISS},
            algorithm=ALGORITHM,
            headers={
                "kid": PUBLIC_KEY_ID,
            },
        )
        return oidc_jwt_token

    oidc_access_token = _mock_access_token(sub=sub, scopes=scopes, target=target)

    # Mock request to get token info
    def _oidc_introspection_callback(request):
        payload = urllib.parse.parse_qs(request.body)
        token = payload["token"][0]
        if token != oidc_access_token:
            return (200, {}, json.dumps({"active": False}))
        return (
            200,
            {},
            json.dumps(
                _mock_oidc_introspection_response(sub=sub, scopes=scopes, target=target)
            ),
        )

    responses.add_callback(
        responses.POST,
        provider_config["introspection_endpoint"],
        callback=protect_oidc_client_basic_callback(
            _oidc_introspection_callback,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        ),
    )

    # Mock request to get ID token
    def _oidc_userinfo_callback(request):
        if sub is None:
            return (401, {}, "")

        user_info = _mock_oidc_user_info_plain_response(
            sub=sub, scopes=scopes, target=target
        )
        if userinfo_response_type == "plain":
            return (200, {"Content-Type": "application/json"}, json.dumps(user_info))
        elif userinfo_response_type == "jwt":
            encoded_user_info = encode_jwt(
                claims=user_info,
                algorithm=ALGORITHM,
                headers={
                    "kid": PUBLIC_KEY_ID,
                },
            )
            return (
                200,
                {"Content-Type": "application/jwt"},
                encoded_user_info,
            )
        else:
            return (400, {}, "")

    responses.add_callback(
        responses.GET,
        provider_config["userinfo_endpoint"],
        callback=protect_oidc_token_callback(
            _oidc_userinfo_callback, access_token=oidc_access_token
        ),
    )

    return oidc_access_token


@pytest.fixture
def access_token():
    """Get opaque OAuth2 access token (fixture)."""
    return _mock_access_token(sub="123|oidc", scopes=["all", "statements/read"])
