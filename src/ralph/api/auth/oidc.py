"""OpenID Connect authentication tool for the Ralph API."""

import logging
from functools import lru_cache
from typing import Dict, Optional, Union, Literal, get_args

import requests
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
    """Pydantic model representing the core of an OpenID Connect UserInfo endpoint response.

    They are common to both the ID token and the UserInfo endpoint.

    They are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        iss (str): Issuer Identifier for the Issuer of the response.
        sub (str): Subject Identifier.
        aud (str or list of str): Audience(s) that this ID Token/UserInfo is intended for.
        exp (int): Expiration time on or after which the ID Token/UserInfo MUST NOT be
                   accepted for processing.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
        target (str): Target for storing the statements.
    """

    iss: str
    sub: str
    aud: Optional[Union[list[str], str]] = None
    exp: float
    iat: float
    scope: Optional[str] = None
    target: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


@lru_cache()
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

def get_user_info(provider_config: dict, access_token: str) -> UserInfo:
    """Get the user's info from the IdP using the /userinfo OIDC endpoint."""
    user_info, is_encoded = get_user_info_data(provider_config["userinfo_endpoint"], access_token)
    if not is_encoded:
        # nothing to do
        return UserInfo.model_validate(user_info)
    return decode_user_info(user_info, provider_config=provider_config)


@lru_cache()
def get_user_info_data(userinfo_endpoint: AnyUrl, access_token: str) -> Union[tuple[dict, Literal[False]], tuple[str, Literal[True]]]:
    """Get the user's info from the IdP using the /userinfo OIDC endpoint.

    The data may be unencoded (Content-Type: 'application/json', in which case it is a json dictionary
    If it is encoded (Content-Type: 'application/jwt', it is a JWT
    see: https://openid.net/specs/openid-connect-core-1_0.html#UserInfo

    Returns the data and whether that data is encoded (a JWT string) or plain (a dict)
    """
    try:
        response = requests.get(
            f"{userinfo_endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        response.raise_for_status()
        content_type = response.headers["Content-Type"]
        return (response.json(), content_type.lower() == "application/jwt")
    except requests.exceptions.RequestException as exc:
        logger.error("Unable to get the user's ID token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def decode_user_info(encoded_user_info: str, provider_config: dict) -> UserInfo:
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
        decoded_token = jwt.decode(
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

    return UserInfo.model_validate(decoded_token)


@lru_cache()
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
    user_info = get_user_info(
        provider_config, access_token=access_token
    )
    return AuthenticatedUser(
        agent={"openid": f"{user_info.iss}/{user_info.sub}"},
        scopes=get_user_scopes(user_info.scope),
        target=user_info.target,
    )
