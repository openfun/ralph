"""Main module for Ralph's LRS API authentication."""

from ralph.api.auth.basic import get_scoped_authenticated_user as get_basic_user
from ralph.api.auth.oidc import get_scoped_authenticated_user as get_oidc_user
from ralph.conf import settings

# At startup, select the authentication mode that will be used
if settings.RUNSERVER_AUTH_BACKEND == settings.AuthBackends.OIDC:
    get_authenticated_user = get_oidc_user
else:
    get_authenticated_user = get_basic_user
