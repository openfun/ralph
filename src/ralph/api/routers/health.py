"""API routes related to application health checking."""

import logging
from inspect import iscoroutinefunction

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from . import DATABASE_CLIENT

logger = logging.getLogger(__name__)

router = APIRouter()


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
    content = {
        "database": (await DATABASE_CLIENT.status()).value
        if iscoroutinefunction(DATABASE_CLIENT.status)
        else DATABASE_CLIENT.status().value
    }
    status_code = (
        status.HTTP_200_OK
        if all(v == "ok" for v in content.values())
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(status_code=status_code, content=content)
