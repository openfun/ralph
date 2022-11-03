"""Authentication & authorization related tools for the Ralph API."""

import json
from functools import lru_cache

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from starlette.authentication import AuthenticationError

from ralph.conf import settings

# Unused password used to avoid timing attacks, by comparing passwords supplied
# with invalid credentials to something innocuous with the same method as if
# it were a legitimate user.
UNUSED_PASSWORD = bcrypt.hashpw(b"ralph", bcrypt.gensalt())


security = HTTPBasic()


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        username(str): Consists of the username of the current user.
        scopes (list): Consists of the scopes the user has access to.
    """

    username: str
    scopes: list[str]


@lru_cache()
def get_stored_credentials(auth_file):
    """Helper to read the credentials/scopes file.

    Reads credentials from JSON file and stored them to avoid reloading them with every
    request.

    Args:
        auth_file (file): Path to the JSON credentiales scope file.

    Returns:
        stored_credentials (json): Cache-memorized credentials.
    """
    try:
        with open(auth_file, encoding=settings.LOCALE_ENCODING) as auth:
            stored_credentials = json.load(auth)
    except FileNotFoundError as exc:
        raise AuthenticationError(f"Credentials file {auth_file} not found.") from exc
    return stored_credentials


def authenticated_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Checks valid auth parameters.

    Gets the basic auth parameters from the Authorization header, and checks them
    against our own list of hashed credentials.

    Args:
        credentials (iterator): auth parameters from the Authorization header


    """
    try:
        user_info = next(
            filter(
                lambda u: u.get("username") == credentials.username,
                get_stored_credentials(settings.AUTH_FILE),
            )
        )
        hashed_password = user_info.get("hash", None)
    except StopIteration:
        # next() gets the first item in the enumerable; if there is none, it raises
        # a StopIteration error as it is out of bounds.
        hashed_password = None
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc

    if not hashed_password:
        # We're doing a bogus password check anyway to avoid
        # timing attacks on usernames
        bcrypt.checkpw(credentials.password.encode("UTF-8"), UNUSED_PASSWORD)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not bcrypt.checkpw(
        credentials.password.encode("UTF-8"), hashed_password.encode("UTF-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return AuthenticatedUser(
        username=credentials.username, scopes=user_info.get("scopes")
    )
