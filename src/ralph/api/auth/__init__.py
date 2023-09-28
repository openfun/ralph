"""Main module for Ralph's LRS API authentication."""

from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials, SecurityScopes

from ralph.api.auth.basic import get_scoped_authenticated_user as get_basic_user, security as basic_security
from ralph.api.auth.oidc import get_scoped_authenticated_user as get_oidc_user
# from ralph.api.auth.user import scope_is_authorized
from ralph.conf import settings

# At startup, select the authentication mode that will be used

if settings.RUNSERVER_AUTH_BACKEND == settings.AuthBackends.OIDC:
    get_authenticated_user = get_oidc_user
else:
    get_authenticated_user = get_basic_user


# def get_authenticated_user(
#     security_scopes: SecurityScopes,
#     credentials: Union[HTTPBasicCredentials, None] = Depends(security),
# ):
#     # Use appropriate method to load user
#     if settings.RUNSERVER_AUTH_BACKEND == settings.AuthBackends.OIDC:
#         user = get_oidc_user() #TODO: add auth_headers variable

#     else:
#         user = get_basic_user(credentials)

#     return user
