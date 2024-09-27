"""Main module for Ralph's LRS API."""

from collections.abc import Callable
from functools import lru_cache
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

import sentry_sdk
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from ralph.conf import settings

from .. import __version__
from .auth import get_authenticated_user
from .auth.user import AuthenticatedUser
from .routers import health, statements, xapi


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
app.include_router(xapi.router)


@app.get("/whoami")
async def whoami(
    user: AuthenticatedUser = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    """Return the current user's username along with their scopes."""
    return {
        "agent": user.agent.model_dump(mode="json", exclude_none=True),
        "scopes": user.scopes,
    }


@app.middleware("http")
async def check_x_experience_api_version_header(
    request: Request, call_next: Callable[[Request], Response]
) -> Response:
    """Check the headers for the X-Experience-API-Version in every request."""
    # about resource doesn't need the "X-Experience-API-Version" header
    if not request.url.path == "/xAPI/about":
        # check that request includes X-Experience-API-Version header
        if "X-Experience-API-Version" not in request.headers:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Missing X-Experience-API-Version header"},
            )

        # check that given X-Experience-API-Version is valid
        if (
            request.headers["X-Experience-API-Version"]
            not in settings.XAPI_VERSIONS_SUPPORTED
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid X-Experience-API-Version header"},
            )

    return await call_next(request)


@app.middleware("http")
async def set_x_experience_api_version_header(
    request: Request, call_next: Callable[[Request], Response]
) -> Response:
    """Set X-Experience-API-Version header in every response."""
    response = await call_next(request)

    if (
        request.headers.get("X-Experience-API-Version")
        in settings.XAPI_VERSIONS_SUPPORTED
    ):
        response.headers["X-Experience-API-Version"] = request.headers[
            "X-Experience-API-Version"
        ]
    else:
        response.headers["X-Experience-API-Version"] = settings.XAPI_VERSION_FALLBACK

    return response


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
