"""API routes related to application health checking"""

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ralph.backends.database.base import BaseDatabase
from ralph.conf import settings

logger = logging.getLogger(__name__)

router = APIRouter()

DATABASE_CLIENT: BaseDatabase = getattr(
    settings.BACKENDS.DATABASE, settings.RUNSERVER_BACKEND.upper()
).get_instance()


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

    content = {"database": DATABASE_CLIENT.status().value}
    status_code = (
        status.HTTP_200_OK
        if all(v == "ok" for v in content.values())
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(status_code=status_code, content=content)
