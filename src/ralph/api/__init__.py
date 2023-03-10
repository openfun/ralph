"""Main module for Ralph's LRS API."""

from contextlib import asynccontextmanager
from inspect import iscoroutinefunction

import sentry_sdk
from fastapi import Depends, FastAPI

from ralph.conf import settings

from .. import __version__
from .auth import AuthenticatedUser, authenticated_user
from .routers import DATABASE_CLIENT, health, statements

if settings.SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_LRS_TRACES_SAMPLE_RATE,
        release=__version__,
        environment=settings.EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
    )


# pylint: disable=redefined-outer-name,unused-argument
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan."""
    # Startup actions goes here
    # [...]

    # We are now ready
    yield

    # Properly shutdown the application
    if hasattr(DATABASE_CLIENT, "close") and callable(DATABASE_CLIENT.close):
        # pylint: disable=expression-not-assigned
        await DATABASE_CLIENT.close() if iscoroutinefunction(
            DATABASE_CLIENT.close
        ) else DATABASE_CLIENT.close()


app = FastAPI(lifespan=lifespan)
app.include_router(statements.router)
app.include_router(health.router)


@app.get("/whoami")
async def whoami(user: AuthenticatedUser = Depends(authenticated_user)):
    """Return the current user's username along with their scopes."""
    return {"username": user.username, "scopes": user.scopes}
