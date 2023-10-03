"""Main module for Ralph's LRS API authentication."""
from pydantic import parse_raw_as

from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBearer, SecurityScopes

from ralph.api.auth.basic import get_authenticated_user as get_basic_user
from ralph.api.auth.oidc import get_authenticated_user as get_oidc_user
from ralph.conf import settings

# At startup, select the authentication mode that will be used
# if :
#     get_authenticated_user = get_oidc_user
# else:
#     get_authenticated_user = get_basic_user


get_authenticated_user = get_basic_user

def get_authenticated_user(*args, **kwargs):
    print("args:", *args)
    print("kwargs:", **kwargs)
    print("header is:",  header)
    print(type(header))
    # if settings.AuthBackend.BASIC in settings.RUNSERVER_AUTH_BACKEND:
    #     try:
    #         print('wayo:', parse_raw_as(header, HTTPBasic))
    #         return get_basic_user(header, security_scopes)
    #     except:
    #         print('Not basic')
    
    # if settings.AuthBackend.OIDC in settings.RUNSERVER_AUTH_BACKEND:
    #     try:
    #         parse_raw_as(header, HTTPBearer)
    #         return get_oidc_user(header, security_scopes)
    #     except:
    #         print('Not oidc')


    # raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Provided headers do not match authorized authentification methods.",
    #     )
