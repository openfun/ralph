"""OpenID Connect authentication tool for the Ralph API."""

import base64
import logging
from functools import lru_cache
from threading import Lock
from typing import Dict, Literal, Optional, Union, get_args

import requests
from cachetools import TTLCache, cached
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OpenIdConnect
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import AnyUrl, BaseModel, ConfigDict
from typing_extensions import Annotated

from ralph.api.auth.user import AuthenticatedUser, Scope, UserScopes
from ralph.conf import settings

OPENID_CONFIGURATION_PATH = "/.well-known/openid-configuration"
oauth2_scheme = OpenIdConnect(
    openIdConnectUrl=f"""{settings.RUNSERVER_AUTH_OIDC_ISSUER_URI}
    {OPENID_CONFIGURATION_PATH}""",
    auto_error=False,
)

# API auth logger
logger = logging.getLogger(__name__)


class UserInfo(BaseModel):
    """Pydantic model representing the UserInfo response of the OIDC IdP.

    They are common to both the ID token and the UserInfo endpoint.
    We do not use it for authentication, so may claims are ignored.
    They are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        sub (str): Subject Identifier.
        scope (str): Scope(s) for resource authorization.
        target (str): Target for storing the statements (custom claim).
    """

    sub: str
    scope: Optional[str] = None
    target: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class TokenIntrospection(BaseModel):
    """Pydantic model representing the Introspection response of the OIDC IdP.

    Based on the RFC 7662 section 2.2 definition of token /introspect response
    This model does not use all fields defined in the RFC,
    and we force some optional fields to be present.

    The 'active' field is assumed to be true and is not included in this model.

    Attributes:
        client_id (str): ID of the client that owns this token
        username (str): Name of the user referred to by this this token, if any
        iss (str): Issuer Identifier for the Issuer of the response.
        sub (str): Subject Identifier, if any
                  No sub means that this is a purely 'client' token
        aud (str or list of str): Audience(s) that this ID Token is intended for.
        exp (int): Expiration time on or after which the ID Token MUST NOT be
                   accepted for processing.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
        target (str): Target for storing the statements (custom claim).

    """

    client_id: str
    username: Optional[str] = None
    token_type: Optional[str] = None
    iss: str
    sub: Optional[str] = None
    aud: Optional[Union[list[str], str]] = None
    exp: float
    iat: float
    scope: Optional[str] = None

    target: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

def make_authenticated_oidc_user(iss: str, user_info: UserInfo) -> AuthenticatedUser:
    """

    """
    return AuthenticatedUser(
        agent={"openid": f"{iss}/{user_info.sub}"},
        scopes=get_user_scopes(user_info.scope),
        target=user_info.target,
    )
def make_authenticated_oidc_client(token_info: TokenIntrospection) -> AuthenticatedUser:
    """

    This is an application token, we don't have a user to get
    So we use the client_id to indentify it instead
    """
    return AuthenticatedUser(
        agent={"openid": f"{token_info.iss}/application/{token_info.client_id}"},
        scopes=get_user_scopes(token_info.scope),
        target=token_info.target,
    )

@lru_cache(maxsize=1)
def discover_provider(base_url: AnyUrl) -> Dict:
    """Discover the authentication server (or OpenId Provider) configuration."""
    try:
        response = requests.get(f"{base_url}{OPENID_CONFIGURATION_PATH}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        logger.error(
            "Unable to discover the authentication server configuration: %s", exc
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_user_info(provider_config: dict, auth_header: str) -> UserInfo:
    """Get the user's info from the IdP using the /userinfo OIDC endpoint."""
    user_info, is_encoded = get_user_info_data(
        userinfo_endpoint=provider_config["userinfo_endpoint"], auth_header=auth_header
    )
    if not is_encoded:
        # nothing to do
        return UserInfo.model_validate(user_info)
    token = decode_jwt_token(user_info, provider_config=provider_config)
    return UserInfo.model_validate(token)


@cached(
    cache=TTLCache(
        maxsize=settings.AUTH_CACHE_MAX_SIZE, ttl=settings.AUTH_OIDC_CACHE_TTL
    ),
    lock=Lock(),
)
def get_user_info_data(
    userinfo_endpoint: AnyUrl, auth_header: str
) -> Union[tuple[dict, Literal[False]], tuple[str, Literal[True]]]:
    """Get the user's info from the IdP using the /userinfo OIDC endpoint.

    The data may be unencoded (Content-Type: 'application/json',
    in which case it is a json dictionary.
    If it is encoded (Content-Type: 'application/jwt', it is a JWT
    see: https://openid.net/specs/openid-connect-core-1_0.html#UserInfo

    Returns the data and whether that data is encoded (a JWT string) or plain (a dict)
    """
    try:
        response = requests.get(
            f"{userinfo_endpoint}",
            headers={"Authorization": auth_header},
            timeout=5,
        )
        response.raise_for_status()
        content_type = response.headers["Content-Type"]
        media_type = content_type.split(";", 1)[0].strip().lower()
        is_jwt = media_type == "application/jwt"
        is_json = media_type == "application/json"
        if not is_jwt and not is_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid Media type in header: {media_type}, "
                    "expected application/jwt or application/json"
                ),
                headers={"WWW-Authenticate": "Bearer"},
            )
        body = response.text if is_jwt else response.json()
        return (body, is_jwt)
    except requests.exceptions.RequestException as exc:
        logger.error("Unable to get the user's ID token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def decode_jwt_token(encoded_user_info: str, provider_config: dict) -> dict:
    """Decode and verify an OpenID Connect ID token."""
    key = get_public_keys(provider_config["jwks_uri"])
    algorithms = provider_config["id_token_signing_alg_values_supported"]
    audience = settings.RUNSERVER_AUTH_OIDC_AUDIENCE
    options = {
        "verify_signature": True,
        "verify_aud": bool(audience),
        "verify_exp": True,
    }
    try:
        return jwt.decode(
            token=encoded_user_info,
            key=key,
            algorithms=algorithms,
            options=options,
            audience=audience,
        )
    except (ExpiredSignatureError, JWTError, JWTClaimsError) as exc:
        logger.error("Unable to decode the ID token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def encode_client_secret_basic_token(client_id: str, client_secret: str) -> str:
    """Encode client id and client secret inside an opaque token.

    Should be sent as Authorization: Basic {token}

    This corresponds to the `client_secret_basic`
    token endpoint authentication method.
    """
    return base64.b64encode(
        client_id.encode("utf-8") + b":" + client_secret.encode("utf-8")
    ).decode("utf-8")


def get_client_basic_auth_header(client_id: str, client_secret: str) -> str:
    """Get a `client_secret_basic` token endpoint authentication header."""
    token = encode_client_secret_basic_token(
        client_id=client_id, client_secret=client_secret
    )
    return f"Basic {token}"


@cached(
    cache=TTLCache(
        maxsize=settings.AUTH_CACHE_MAX_SIZE, ttl=settings.AUTH_OIDC_CACHE_TTL
    ),
    lock=Lock(),
)
def get_token_introspection(
    introspection_endpoint: AnyUrl, token: str, client_basic_auth_header: str
) -> TokenIntrospection:
    """Get info on given token from the IdP using /introspection OIDC endpoint."""
    token_info = None
    try:
        response = requests.post(
            f"{introspection_endpoint}",
            headers={"Authorization": client_basic_auth_header},
            data={
                "token": f"{token}",
            },
            timeout=5,
        )
        response.raise_for_status()
        token_info = response.json()
    except requests.exceptions.RequestException as exc:
        logger.error("Unable to get token info: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if not token_info["active"]:
        logger.error("Inactive or invalid token info.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenIntrospection.model_validate(token_info)


@lru_cache(maxsize=1)
def get_public_keys(jwks_uri: AnyUrl) -> Dict:
    """Retrieve the public keys used by the provider server for signing."""
    try:
        response = requests.get(jwks_uri, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        logger.error(
            (
                "Unable to retrieve the public keys used by the provider server"
                "for signing: %s"
            ),
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_user_scopes(oidc_scopes: Optional[str]) -> UserScopes:
    """Extract Ralph's custom OAuth2 scopes from the global scope list.

    Ignore incompatible scopes.
    """
    compatible_scopes = (
        [scope for scope in oidc_scopes.split(" ") if scope in get_args(Scope)]
        if oidc_scopes
        else []
    )
    return UserScopes(compatible_scopes)

def _can_query_user_info(provider_config: dict) -> bool:
    """Check whether the IdP can be queried for `UserInfo` using an access token.
    
    True when Ralph has client credentials and the IdP exposes
    both `/introspect` and `/userinfo` endpoints.
    """
    return bool(
        settings.RUNSERVER_AUTH_OIDC_CLIENT_ID
        and settings.RUNSERVER_AUTH_OIDC_CLIENT_SECRET
        and provider_config.get("introspection_endpoint")
        and provider_config.get("userinfo_endpoint")
    )

def get_oidc_user(
    auth_header: Annotated[Optional[HTTPBearer], Depends(oauth2_scheme)],
) -> AuthenticatedUser:
    """Decode and validate OpenId Connect ID token against issuer in config.

    Args:
        auth_header (str): Authentication header containing the Base64 encoded
            OIDC Token. This is invoked behind the scenes by Depends.
        security_scopes (SecurityScopes): Scopes required to access the endpoint.

    Return:
        AuthenticatedUser (AuthenticatedUser)

    Raises:
        HTTPException
    """
    if auth_header is None or "bearer" not in auth_header.lower():
        logger.debug(
            "Not using OIDC auth. The OpenID Connect authentication mode requires a "
            "Bearer token"
        )
        return None

    access_token = auth_header.split(" ")[-1]
    provider_config = discover_provider(settings.RUNSERVER_AUTH_OIDC_ISSUER_URI)

    if not _can_query_user_info(provider_config):
        # We have to assume that the access token is an ID Token
        # in the JWT format, and can be decoded offline.
        id_token = decode_jwt_token(encoded_user_info=access_token, provider_config=provider_config)
        user_info = UserInfo.model_validate(id_token)
        return make_authenticated_oidc_user(iss=id_token["iss"],user_info=user_info)

    client_basic_auth_header = get_client_basic_auth_header(
        client_id=settings.RUNSERVER_AUTH_OIDC_CLIENT_ID,
        client_secret=settings.RUNSERVER_AUTH_OIDC_CLIENT_SECRET,
    )

    token_info = get_token_introspection(
        provider_config["introspection_endpoint"],
        token=access_token,
        client_basic_auth_header=client_basic_auth_header,
    )

    if not token_info.sub:
        return make_authenticated_oidc_client(token_info)
    else:
        # This is a real user, we can retrieve their user info
        user_info = get_user_info(provider_config, auth_header=auth_header)
        if user_info.sub != token_info.sub:
            logger.error(
                ("Inconsistent token subject: %s != %s"), user_info.sub, token_info.sub
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return make_authenticated_oidc_user(iss=token_info.iss, user_info=user_info)
