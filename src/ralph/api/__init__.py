"""
Main module for Ralph's LRS API.
"""
import sentry_sdk
from fastapi import Depends, FastAPI

from ralph.conf import settings

from .. import __version__
from .auth import AuthenticatedUser, authenticated_user
from .routers import health, statements

if settings.SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        release=__version__,
        environment=settings.EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
    )

app = FastAPI()
app.include_router(statements.router)
app.include_router(health.router)


@app.get("/whoami")
async def whoami(user: AuthenticatedUser = Depends(authenticated_user)):
    """
    Return the current user's username along with their scopes.
    """
    return {"username": user.username, "scopes": user.scopes}
