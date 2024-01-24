"""API routes related to application health checking."""

import logging
from typing import Union

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from ralph.backends.data.base import DataBackendStatus
from ralph.backends.loader import get_lrs_backends
from ralph.backends.lrs.base import BaseAsyncLRSBackend, BaseLRSBackend
from ralph.conf import settings
from ralph.utils import await_if_coroutine, get_backend_class

logger = logging.getLogger(__name__)

router = APIRouter()

BACKEND_CLIENT: Union[BaseLRSBackend, BaseAsyncLRSBackend] = get_backend_class(
    backends=get_lrs_backends(), name=settings.RUNSERVER_BACKEND
)()


class Heartbeat(BaseModel):
    """Ralph backends status."""

    database: DataBackendStatus

    @property
    def is_alive(self):
        """A helper that checks the overall status."""
        return self.database == DataBackendStatus.OK


@router.get("/__lbheartbeat__")
async def lbheartbeat() -> None:
    """Load balancer heartbeat.

    Return a 200 when the server is running.
    """
    return


@router.get("/__heartbeat__", status_code=status.HTTP_200_OK)
async def heartbeat(response: Response) -> Heartbeat:
    """Application heartbeat.

    Return a 200 if all checks are successful.
    """
    statuses = Heartbeat.model_construct(
        database=await await_if_coroutine(BACKEND_CLIENT.status())
    )
    if not statuses.is_alive:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return statuses
