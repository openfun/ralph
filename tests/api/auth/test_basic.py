"""Tests for basic authentication for the Ralph API."""

import base64
import json

import bcrypt
import pytest
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasicCredentials

from ralph.api.auth.basic import (
    ServerUsersCredentials,
    UserCredentials,
    get_basic_auth_user,
    get_stored_credentials,
)
from ralph.api.auth.user import AuthenticatedUser, UserScopes
from ralph.conf import AuthBackend, Settings, settings

from tests.helpers import configure_env_for_mock_oidc_auth

STORED_CREDENTIALS = json.dumps(
    [
        {
            "username": "ralph",
            "hash": bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("UTF-8"),
            "scopes": ["statements/read/mine", "statements/write"],
            "agent": {"mbox": "mailto:ralph@example.com"},
            "target": "custom_target",
        }
    ]
)


def test_api_auth_basic_model_serveruserscredentials():
    """Test api.auth ServerUsersCredentials model."""

    users = ServerUsersCredentials(
        __root__=[
            UserCredentials(
                username="johndoe",
                hash="notrealhash",
                scopes=["statements/read/mine", "statements/write"],
                agent={"mbox": "mailto:johndoe@example.com"},
            ),
            UserCredentials(
                username="foo",
                hash="notsorealhash",
                scopes=["all"],
                agent={"mbox": "mailto:foo@example.com"},
                target="foo",
            ),
        ]
    )
    other_users = ServerUsersCredentials.parse_obj(
        [
            UserCredentials(
                username="janedoe",
                hash="notreallyrealhash",
                scopes=["statements/read/mine", "statements/write"],
                agent={"mbox": "mailto:janedoe@example.com"},
            ),
        ]
    )

    # Test addition operator
    users += other_users

    # Test len
    assert len(users) == 3

    # Test getitem
    assert users[0].username == "johndoe"
    assert users[1].username == "foo"
    assert users[2].username == "janedoe"

    # Test iterator
    usernames = [user.username for user in users]
    assert len(usernames) == 3
    assert usernames == ["johndoe", "foo", "janedoe"]

    # Test username uniqueness validator
    with pytest.raises(
        ValueError,
        match="You cannot create multiple credentials with the same username",
    ):
        users += ServerUsersCredentials.parse_obj(
            [
                UserCredentials(
                    username="foo",
                    hash="notsorealhash",
                    scopes=["statements/read/mine", "statements/write"],
                    agent={"mbox": "mailto:foo2@example.com"},
                ),
            ]
        )


def test_api_auth_basic_caching_credentials(fs):
    """Test the caching of HTTP basic auth credentials."""

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)
    get_basic_auth_user.cache_clear()
    get_stored_credentials.cache_clear()

    credentials = HTTPBasicCredentials(username="ralph", password="admin")

    # Call function as in a first request with these credentials
    get_basic_auth_user(credentials=credentials)

    assert get_basic_auth_user.cache.popitem() == (
        ("ralph", "admin"),
        AuthenticatedUser(
            agent={"mbox": "mailto:ralph@example.com"},
            scopes=UserScopes(["statements/read/mine", "statements/write"]),
            target="custom_target",
        ),
    )


def test_api_auth_basic_with_wrong_password(fs):
    """Test the authentication with a wrong password."""

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)
    get_basic_auth_user.cache_clear()

    credentials = HTTPBasicCredentials(username="ralph", password="wrong_password")

    # Call function as in a first request with these credentials
    with pytest.raises(HTTPException):
        get_basic_auth_user(credentials)


def test_api_auth_basic_no_credential_file_found(fs, monkeypatch):
    """Test that, without a credential file, authentication fails."""

    monkeypatch.setenv("RALPH_AUTH_FILE", "other_file")
    monkeypatch.setattr("ralph.api.auth.basic.settings", Settings())
    get_basic_auth_user.cache_clear()

    credentials = HTTPBasicCredentials(username="ralph", password="admin")

    with pytest.raises(HTTPException):
        get_basic_auth_user(credentials)


@pytest.mark.anyio
async def test_api_auth_basic_get_whoami_no_credentials(client):
    """Whoami route returns a 401 error when no credentials are sent."""
    response = await client.get("/whoami")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.anyio
async def test_api_auth_basic_get_whoami_credentials_encoding_error(client):
    """Whoami route returns a 401 error when the credentials encoding is broken."""
    response = await client.get(
        "/whoami", headers={"Authorization": "Basic not-base64"}
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.anyio
async def test_api_auth_basic_get_whoami_username_not_found(fs, client):
    """Whoami route returns a 401 error when the username cannot be found."""
    credential_bytes = base64.b64encode("john:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")
    get_basic_auth_user.cache_clear()

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)

    response = await client.get(
        "/whoami", headers={"Authorization": f"Basic {credentials}"}
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.anyio
async def test_api_auth_basic_get_whoami_wrong_password(fs, client):
    """Whoami route returns a 401 error when the password is wrong."""
    credential_bytes = base64.b64encode("john:not-admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)
    get_basic_auth_user.cache_clear()

    response = await client.get(
        "/whoami", headers={"Authorization": f"Basic {credentials}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "runserver_auth_backends",
    [[AuthBackend.BASIC, AuthBackend.OIDC], [AuthBackend.BASIC]],
)
async def test_api_auth_basic_get_whoami_correct_credentials(
    fs, monkeypatch, runserver_auth_backends, client
):
    """Whoami returns a 200 response when the credentials are correct.

    Return the username and associated scopes.
    """
    configure_env_for_mock_oidc_auth(monkeypatch, runserver_auth_backends)

    credential_bytes = base64.b64encode("ralph:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)
    get_basic_auth_user.cache_clear()

    response = await client.get(
        "/whoami", headers={"Authorization": f"Basic {credentials}"}
    )

    assert response.status_code == 200

    assert len(response.json().keys()) == 2
    assert response.json()["agent"] == {"mbox": "mailto:ralph@example.com"}
    assert sorted(response.json()["scopes"]) == [
        "statements/read/mine",
        "statements/write",
    ]


@pytest.mark.anyio
async def test_api_auth_basic_get_whoami_invalid_backend(fs, monkeypatch, client):
    """Check for an exception when providing valid credentials when Basic
    authentication is not supported.
    """
    configure_env_for_mock_oidc_auth(monkeypatch, [AuthBackend.OIDC])

    credential_bytes = base64.b64encode("ralph:admin".encode("utf-8"))
    credentials = str(credential_bytes, "utf-8")

    auth_file_path = settings.APP_DIR / "auth.json"
    fs.create_file(auth_file_path, contents=STORED_CREDENTIALS)
    get_basic_auth_user.cache_clear()

    response = await client.get(
        "/whoami", headers={"Authorization": f"Basic {credentials}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}
