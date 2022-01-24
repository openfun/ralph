"""
Authentication & authorization related tools for the Ralph API.
"""
import json
from functools import lru_cache
from typing import List

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from starlette.authentication import AuthenticationError

from ralph.defaults import AUTH_FILE, LOCALE_ENCODING

# Unused password used to avoid timing attacks, by comparing passwords supplied
# with invalid credentials to something innocuous with the same method as if
# it were a legitimate user.
UNUSED_PASSWORD = bcrypt.hashpw(b"ralph", bcrypt.gensalt())


security = HTTPBasic()


class AuthenticatedUser(BaseModel):
    """
    Base User class used for authentication purposes. Carries the username
    as well as the scopes the user has access to.
    """

    username: str
    scopes: List[str]


@lru_cache()
def get_stored_credentials(auth_file):
    """
    Helper to read the credentials/scopes file to JSON and memoize it so we do not
    reload it with every request.
    """
    try:
        with open(auth_file, encoding=LOCALE_ENCODING) as auth:
            stored_credentials = json.load(auth)
    except FileNotFoundError as exc:
        raise AuthenticationError(f"Credentials file {auth_file} not found.") from exc
    return stored_credentials


def authenticated_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Get the basic auth parameters from the Authorization header, and check them
    against our own list of hashed credentials.
    """
    try:
        user_info = next(
            filter(
                lambda u: u.get("username") == credentials.username,
                get_stored_credentials(AUTH_FILE),
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
