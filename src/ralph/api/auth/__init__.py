"""Main module for Ralph's LRS API authentication."""
from pydantic import parse_obj_as

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBearer, SecurityScopes
from fastapi.security.http import HTTPBase

from ralph.api.auth.basic import get_authenticated_user as get_basic_user
from ralph.api.auth.oidc import get_authenticated_user as get_oidc_user
from ralph.conf import settings

def get_authenticated_user(
    security_scopes: SecurityScopes = SecurityScopes([]),
    basic_auth_user = Depends(get_basic_user), 
    oidc_auth_user = Depends(get_oidc_user), 
    ):

    if basic_auth_user is not None:
        user = basic_auth_user
        auth_method = "Basic"
    elif oidc_auth_user is not None:
        user = oidc_auth_user
        auth_method = "Bearer"
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials", # TODO: add supported auth methods
        )

    # Restrict access by scopes
    if settings.LRS_RESTRICT_BY_SCOPES:
        for requested_scope in security_scopes.scopes:
            is_auth = user.scopes.is_authorized(requested_scope)
            if not is_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f'Access not authorized to scope: "{requested_scope}".',
                    headers={"WWW-Authenticate": auth_method},
                )

    return user