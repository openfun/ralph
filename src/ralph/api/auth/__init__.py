"""Main module for Ralph's LRS API authentication."""

from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes

from ralph.api.auth.basic import get_basic_auth_user
from ralph.api.auth.oidc import get_oidc_user
from ralph.conf import AuthBackend, settings


def get_authenticated_user(
    security_scopes: SecurityScopes = SecurityScopes([]),
    basic_auth_user=Depends(get_basic_auth_user),
    oidc_auth_user=Depends(get_oidc_user),
):
    """Authenticate user with any allowed method, using credentials in the header."""
    if AuthBackend.BASIC not in settings.RUNSERVER_AUTH_BACKENDS:
        basic_auth_user = None
    if AuthBackend.OIDC not in settings.RUNSERVER_AUTH_BACKENDS:
        oidc_auth_user = None

    if basic_auth_user is not None:
        user = basic_auth_user
        auth_method = "Basic"
    elif oidc_auth_user is not None:
        user = oidc_auth_user
        auth_method = "Bearer"
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={
                "WWW-Authenticate": ",".join(
                    [val.value for val in settings.RUNSERVER_AUTH_BACKENDS]
                )
            },
        )

    # Restrict access by scopes
    if settings.LRS_RESTRICT_BY_SCOPES:
        for requested_scope in security_scopes.scopes:
            if not user.scopes.is_authorized(requested_scope):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f'Access not authorized to scope: "{requested_scope}".',
                    headers={"WWW-Authenticate": auth_method},
                )
    return user
