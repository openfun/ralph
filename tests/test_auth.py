"""Tests for authentication for the Ralph API."""

import base64
import json

import bcrypt
from fastapi.security import HTTPBasicCredentials
from fastapi.testclient import TestClient

from ralph.api import app
from ralph.api.auth import AuthenticatedUser, authenticated_user
from ralph.conf import settings

client = TestClient(app)


STORED_CREDENTIALS = json.dumps(
    [
        {
            "username": "ralph",
            "hash": bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("UTF-8"),
            "scopes": ["ralph_test_scope"],
        }
    ]
)


def test_get_whoami_no_credentials():
    """Whoami route returns a 401 error when no credentials are sent."""
    response = client.get("/whoami")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Not authenticated"}


def test_get_whoami_credentials_wrong_scheme():
    """Whoami route returns a 401 error when wrong scheme is used for authorization."""
    response = client.get("/whoami", headers={"Authorization": "Bearer sometoken"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Not authenticated"}


def test_get_whoami_credentials_encoding_error():
    """Whoami route returns a 401 error when the credentials encoding is broken."""
    response = client.get("/whoami", headers={"Authorization": "Basic not-base64"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}


# pylint: disable=invalid-name
def test_get_whoami_username_not_found(fs):
    """Whoami route returns a 401 error when the username cannot be found."""
    credential_bytes = base64.b64encode("john:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    response = client.get("/whoami", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}


# pylint: disable=invalid-name
def test_get_whoami_wrong_password(fs):
    """Whoami route returns a 401 error when the password is wrong."""
    credential_bytes = base64.b64encode("john:not-admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    response = client.get("/whoami", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}


# pylint: disable=invalid-name
def test_get_whoami_correct_credentials(fs):
    """Whoami returns a 200 response when the credentials are correct.

    Returns the username and associated scopes.
    """
    credential_bytes = base64.b64encode("ralph:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    response = client.get("/whoami", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 200
    assert response.json() == {
        "username": "ralph",
        "scopes": ["ralph_test_scope"],
    }


def test_api_auth_caching_credentials(fs):
    """Test the caching of HTTP basic auth credentials."""

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    credentials = HTTPBasicCredentials(username="ralph", password="admin")

    # Call function as in a first request with these credentials
    authenticated_user(credentials)

    assert authenticated_user.cache.popitem() == (
        ("ralph", "admin"),
        AuthenticatedUser(username="ralph", scopes=["ralph_test_scope"]),
    )
