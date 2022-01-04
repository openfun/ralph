"""
Tests for authentication for the Ralph API.
"""
import base64
import json

import bcrypt
from fastapi.testclient import TestClient

from ralph.api import app
from ralph.defaults import APP_DIR

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
    """
    whoami route returns a 400 error when no credentials are sent.
    """
    response = client.get("/whoami")
    assert response.status_code == 400
    assert response.json() == {"error": "Missing authentication credentials."}


def test_get_whoami_credentials_wrong_scheme():
    """
    whoami route returns a 400 error when the wrong scheme is used for authorization.
    """
    response = client.get("/whoami", headers={"Authorization": "Bearer sometoken"})
    assert response.status_code == 400
    assert response.json() == {"error": "Missing authentication credentials."}


def test_get_whoami_credentials_encoding_error():
    """
    whoami route returns a 400 error when the credentials' encoding is broken.
    """
    response = client.get("/whoami", headers={"Authorization": "Basic not-base64"})
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid authentication credentials."}


# pylint: disable=invalid-name
def test_get_whoami_credentials_username_not_found(fs):
    """
    whoami route returns a 400 error when the credentials' username cannot be found.
    """
    credential_bytes = base64.b64encode("john:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    response = client.get("/whoami", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid authentication credentials."}


# pylint: disable=invalid-name
def test_get_whoami_wrong_password(fs):
    """
    whoami route returns a 400 error when the credentials' password is wrong.
    """
    credential_bytes = base64.b64encode("john:not-admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    response = client.get("/whoami", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid authentication credentials."}


# pylint: disable=invalid-name
def test_get_whoami_correct_credentials(fs):
    """
    whoami returns a 200 response with the username and associated scopes when
    the credentials are correct.
    """
    credential_bytes = base64.b64encode("ralph:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    response = client.get("/whoami", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 200
    assert response.json() == {
        "username": "ralph",
        "scopes": ["authenticated", "ralph_test_scope"],
    }
