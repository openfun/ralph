"""API routes related to application health checking."""

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ralph.backends.conf import backends_settings
from ralph.backends.lrs.base import BaseLRSBackend
from ralph.conf import settings
from ralph.utils import await_if_coroutine, get_backend_instance

logger = logging.getLogger(__name__)

router = APIRouter()

BACKEND_CLIENT: BaseLRSBackend = get_backend_instance(
    backend_type=backends_settings.BACKENDS.LRS,
    backend_name=settings.RUNSERVER_BACKEND,
)


@router.get("/__lbheartbeat__")
async def lbheartbeat():
    """Load balancer heartbeat.

    Returns a 200 when the server is running.
    """
    return


@router.get("/__heartbeat__")
async def heartbeat():
    """Application heartbeat.

    Returns a 200 if all checks are successful.
    """
    content = {"database": await await_if_coroutine(BACKEND_CLIENT.status().value)}
    status_code = (
        status.HTTP_200_OK
        if all(v == "ok" for v in content.values())
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(status_code=status_code, content=content)
