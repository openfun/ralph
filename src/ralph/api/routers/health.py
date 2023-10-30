"""API routes related to application health checking."""

import logging
from typing import Union

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ralph.backends.loader import get_lrs_backends
from ralph.backends.lrs.base import BaseAsyncLRSBackend, BaseLRSBackend
from ralph.conf import settings
from ralph.utils import await_if_coroutine, get_backend_class

logger = logging.getLogger(__name__)

router = APIRouter()

BACKEND_CLIENT: Union[BaseLRSBackend, BaseAsyncLRSBackend] = get_backend_class(
    backends=get_lrs_backends(), name=settings.RUNSERVER_BACKEND
)()


@router.get("/__lbheartbeat__")
async def lbheartbeat() -> None:
    """Load balancer heartbeat.

    Return a 200 when the server is running.
    """
    return


@router.get("/__heartbeat__")
async def heartbeat() -> JSONResponse:
    """Application heartbeat.

    Return a 200 if all checks are successful.
    """
    content = {"database": (await await_if_coroutine(BACKEND_CLIENT.status())).value}
    status_code = (
        status.HTTP_200_OK
        if all(v == "ok" for v in content.values())
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(status_code=status_code, content=content)
