"""Tests for middlewares of the Ralph API."""

import pytest
from httpx import AsyncClient

from ralph.api import app


@pytest.mark.anyio
async def test_x_experience_api_version_header(basic_auth_credentials):
    """
    Test X-Experience-API-Version header is checked in request and included in response.
    """

    async with AsyncClient(
        app=app,
        base_url="http://testserver",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    ) as client:
        # Check for 400 status code when X-Experience-API-Version header is not included
        response = await client.get(
            "/xAPI/statements/",
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Missing X-Experience-API-Version header"}
        assert "X-Experience-API-Version" in response.headers
        assert response.headers["X-Experience-API-Version"] == "1.0.3"

        # Check that X-Experience-API-Version header is included in response
        response = await client.get(
            "/xAPI/statements/",
            headers={"X-Experience-API-Version": "1.0.3"},
        )

        assert response.status_code == 200
        assert "X-Experience-API-Version" in response.headers
        assert response.headers["X-Experience-API-Version"] == "1.0.3"

        # Check for 400 status code when X-Experience-API-Version header
        # is included but unsupported
        response = await client.get(
            "/xAPI/statements/",
            headers={"X-Experience-API-Version": "1.0.4"},
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid X-Experience-API-Version header"}
        assert "X-Experience-API-Version" in response.headers
        assert response.headers["X-Experience-API-Version"] == "1.0.3"
