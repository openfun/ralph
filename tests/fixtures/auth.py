"""Test fixtures related to authentication on the API."""
import base64
import json

import bcrypt
import pytest

from ralph.conf import settings


# pylint: disable=invalid-name
@pytest.fixture
def auth_credentials(fs):
    """Sets up the credentials file for request authentication.

    Returns:
        credentials (str): auth parameters that need to be passed
            through headers to authenticate the request.
    """
    credential_bytes = base64.b64encode("ralph:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(
        auth_file_path,
        contents=json.dumps(
            [
                {
                    "username": "ralph",
                    "hash": bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("UTF-8"),
                    "scopes": ["ralph_test_scope"],
                }
            ]
        ),
    )

    return credentials
