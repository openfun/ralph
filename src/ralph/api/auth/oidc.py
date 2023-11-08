"""OpenID Connect authentication tool for the Ralph API."""

import logging
from functools import lru_cache
from typing import Dict, Optional

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import OpenIdConnect, SecurityScopes
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import AnyUrl, BaseModel, Extra
from typing_extensions import Annotated

from ralph.api.auth.user import AuthenticatedUser, UserScopes
from ralph.conf import settings

OPENID_CONFIGURATION_PATH = "/.well-known/openid-configuration"
oauth2_scheme = OpenIdConnect(
    openIdConnectUrl=f"""{settings.RUNSERVER_AUTH_OIDC_ISSUER_URI}
    {OPENID_CONFIGURATION_PATH}""",
    auto_error=False,
)

# API auth logger
logger = logging.getLogger(__name__)


class IDToken(BaseModel):
    """Pydantic model representing the core of an OpenID Connect ID Token.

    ID Tokens are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        iss (str): Issuer Identifier for the Issuer of the response.
        sub (str): Subject Identifier.
        aud (str): Audience(s) that this ID Token is intended for.
        exp (int): Expiration time on or after which the ID Token MUST NOT be
                   accepted for processing.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
    """

    iss: str
    sub: str
    aud: Optional[str]
    exp: int
    iat: int
    scope: Optional[str]

    class Config:  # noqa: D106
        extra = Extra.ignore


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


def get_oidc_user(
    auth_header: Annotated[Optional[str], Depends(oauth2_scheme)],
    security_scopes: SecurityScopes = SecurityScopes([]),
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
    if auth_header is None or "Bearer" not in auth_header:
        logger.error("The OpenID Connect authentication mode requires a Bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    id_token = auth_header.split(" ")[-1]
    provider_config = discover_provider(settings.RUNSERVER_AUTH_OIDC_ISSUER_URI)
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
            token=id_token,
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

    id_token = IDToken.parse_obj(decoded_token)

    user = AuthenticatedUser(
        agent={"openid": f"{id_token.iss}/{id_token.sub}"},
        scopes=UserScopes(id_token.scope.split(" ") if id_token.scope else []),
    )

    # Restrict access by scopes
    if settings.LRS_RESTRICT_BY_SCOPES:
        for requested_scope in security_scopes.scopes:
            if not user.scopes.is_authorized(requested_scope):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f'Access not authorized to scope: "{requested_scope}".',
                    headers={"WWW-Authenticate": "Basic"},
                )

    return user
