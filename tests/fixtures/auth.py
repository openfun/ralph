"""Test fixtures related to authentication on the API."""
import base64
import json
import os

import bcrypt
import pytest

from ralph.api.auth import get_stored_credentials
from ralph.conf import settings


def create_user(fs_, username: str, password: str, scopes: list, agent: dict):
    """Create a user using Basic Auth in the (fake) file system.

    Args:
        fs_: fixture provided by pyfakefs
        username: username used for auth
        password: password used for auth
        scopes (List[str]): list of scopes available to the user
        agent (dict): an agent that represents the user and may be used as authority
    """
    credential_bytes = base64.b64encode(f"{username}:{password}".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")
    auth_file_path = settings.AUTH_FILE  # settings.APP_DIR / "auth.json"

    # Clear lru_cache to allow for auth testing within same function
    get_stored_credentials.cache_clear()

    all_users = []
    if os.path.exists(auth_file_path):
        with open(auth_file_path, encoding="utf-8") as file:
            all_users = json.loads(file.read())
        os.remove(auth_file_path)

    user = {
        "username": username,
        "hash": bcrypt.hashpw(bytes(password.encode("utf-8")), bcrypt.gensalt()).decode(
            "UTF-8"
        ),
        "scopes": scopes,
        "agent": agent,
    }
    all_users.append(user)

    fs_.create_file(auth_file_path, contents=json.dumps(all_users))

    return credentials


# pylint: disable=invalid-name
@pytest.fixture
def auth_credentials(fs, user_scopes=None, agent=None):
    """Sets up the credentials file for request authentication.

    Args:
        fs: fixture provided by pyfakefs (not called in the code)
        user_scopes (List[str]): list of scopes to associate to the user

    Returns:
        credentials (str): auth parameters that need to be passed
            through headers to authenticate the request.
        user_scopes (List[str]): list of scopes for the created user
        agent (dict): valid Agent (per xAPI specification) representing the user
    """

    username = "ralph"
    password = "admin"
    if user_scopes is None:
        user_scopes = ["all"]
    if agent is None:
        agent = {"mbox": "mailto:test_ralph@example.com"}

    credentials = create_user(fs, username, password, user_scopes, agent)

    return credentials
