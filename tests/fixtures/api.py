"""Test fixtures related to the API."""

import pytest
from httpx import AsyncClient

from ralph.api import app


@pytest.mark.anyio
@pytest.fixture(scope="session")
async def client():
    """Return an AsyncClient for the FastAPI app."""

    async with AsyncClient(app=app, base_url="http://test") as async_client:
        yield async_client
