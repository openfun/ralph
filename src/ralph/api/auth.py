"""
Authentication & authorization related tools for the Ralph API.
"""
import base64
import binascii
import json
from functools import lru_cache

import bcrypt
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
)

from ralph.defaults import AUTH_FILE, LOCALE_ENCODING

# Unused password used to avoid timing attacks, by comparing passwords supplied
# with invalid credentials to something innocuous with the same method as if
# it were a legitimate user.
UNUSED_PASSWORD = bcrypt.hashpw(b"ralph", bcrypt.gensalt())


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


class BasicAuthBackend(AuthenticationBackend):
    """
    Custom authentication backend that verifies user credentials passed through
    basic auth and sets up the user's allowed scopes.
    """

    # pylint: disable=arguments-renamed
    async def authenticate(self, request: Request):
        """
        Get the basic auth parameters from the Authorization header, and check them
        against our own list of hashed credentials.
        """
        if "Authorization" not in request.headers:
            raise AuthenticationError("Missing authentication credentials.")

        # Extract basic auth credentials from the relevant header
        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                raise AuthenticationError("Missing authentication credentials.")
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError("Invalid authentication credentials.") from exc

        # Split username/password and check them against our stored user credentials
        username, password = decoded.split(":")
        try:
            user_info = next(
                filter(
                    lambda u: u.get("username") == username,
                    get_stored_credentials(AUTH_FILE),
                )
            )
            hashed_password = user_info.get("hash", None)
        except StopIteration:
            # next() gets the first item in the enumerable; if there is none, it raises
            # a StopIteration error as it is out of bounds.
            hashed_password = None

        if not hashed_password:
            # We're doing a bogus password check anyway to avoid
            # timing attacks on usernames
            bcrypt.checkpw(password.encode("UTF-8"), UNUSED_PASSWORD)
            raise AuthenticationError("Invalid authentication credentials.")

        if not bcrypt.checkpw(
            password.encode("UTF-8"), hashed_password.encode("UTF-8")
        ):
            raise AuthenticationError("Invalid authentication credentials.")

        return AuthCredentials(["authenticated", *user_info.get("scopes")]), SimpleUser(
            username
        )


# pylint: disable=unused-argument
def on_auth_error(request: Request, exc: Exception):
    """
    Format authentication errors as JSON Responses. Keep the default
    error code 400 from starlette.
    """
    return JSONResponse({"error": str(exc)}, status_code=400)
