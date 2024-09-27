"""Tests for the GET about endpoint of the Ralph API."""

import pytest


@pytest.mark.anyio
async def test_xapi_about_get(client, basic_auth_credentials):
    """Test the about API route (without X-Experience-API-Version request header)."""

    response = await client.get(
        "/xAPI/about", headers={"Authorization": f"Basic {basic_auth_credentials}"}
    )

    assert response.status_code == 200
    assert "1.0.3" in response.json()["version"]
