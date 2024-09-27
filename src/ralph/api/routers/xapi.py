"""API routes related to other routes of the xAPI standard."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ralph.conf import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/xAPI")


@router.get("/about")
async def about():
    """Return information about this LRS, including the xAPI version supported."""
    return JSONResponse(
        {
            "version": settings.XAPI_VERSIONS_SUPPORTED,
            "extensions": {
                "xapi": {
                    "statements": {
                        "name": "Statements",
                        "methods": ["GET", "POST", "PUT", "HEAD"],
                        "endpoint": "/xAPI/statements",
                        "description": (
                            "Endpoint to submit and retrieve XAPI statements."
                        ),
                    }
                }
            },
        }
    )
