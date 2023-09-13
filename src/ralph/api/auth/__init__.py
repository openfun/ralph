"""Main module for Ralph's LRS API authentication."""

from typing import Union 

from fastapi import Depends, security
from fastapi.security import HTTPBasicCredentials, SecurityScopes

from ralph.api.auth.basic import get_authenticated_user as get_basic_user
from ralph.api.auth.oidc import get_authenticated_user as get_oidc_user
from ralph.conf import settings

# At startup, select the authentication mode that will be used


def get_authenticated_user(
    security_scopes: SecurityScopes,
    credentials: Union[HTTPBasicCredentials, None] = Depends(security),
):
    
    # Use appropriate method to load user
    if settings.RUNSERVER_AUTH_BACKEND == settings.AuthBackends.OIDC:
        user = get_oidc_user()
    
    else:
        user = get_basic_user(credentials)

    # Restrict access by scopes #TODO: do this for OIDC 
    if settings.LRS_RESTRICT_BY_SCOPES:
        for requested_scope in security_scopes.scopes:
            if not scope_is_authorized(requested_scope, tuple(user.scopes)):
                #print(f"Requested scope `{requested_scope}` is not authorized for this user ({user.scopes})")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f'Access not authorized to scope: "{requested_scope}".',
                    headers={"WWW-Authenticate": "Basic"},
                )
    return user

