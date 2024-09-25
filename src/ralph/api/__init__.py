"""Main module for Ralph's LRS API."""

from functools import lru_cache
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

import sentry_sdk
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ralph.conf import settings

from .. import __version__
from .auth import get_authenticated_user
from .auth.user import AuthenticatedUser
from .routers import health, statements


@lru_cache(maxsize=None)
def get_health_check_routes() -> List:
    """Return the health check routes."""
    return [route.path for route in health.router.routes]


def filter_transactions(event: Dict, hint) -> Union[Dict, None]:  # noqa: ARG001
    """Filter transactions for Sentry."""
    url = urlparse(event["request"]["url"])

    if settings.SENTRY_IGNORE_HEALTH_CHECKS and url.path in get_health_check_routes():
        return None

    return event


if settings.SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_LRS_TRACES_SAMPLE_RATE,
        release=__version__,
        environment=settings.EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
        before_send_transaction=filter_transactions,
    )

app = FastAPI()
app.include_router(statements.router)
app.include_router(health.router)


@app.get("/whoami")
async def whoami(
    user: AuthenticatedUser = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    """Return the current user's username along with their scopes."""
    return {
        "agent": user.agent.model_dump(mode="json", exclude_none=True),
        "scopes": user.scopes,
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Called on invalid request data, return error detail as json response."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc.errors())},
    )


@app.exception_handler(TypeError)
async def type_exception_handler(_: Request, exc: TypeError) -> JSONResponse:
    """Called on bad type or value, return error detail as json response."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )
