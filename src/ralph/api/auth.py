"""Authentication & authorization related tools for the Ralph API."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, SecurityScopes
from pydantic import BaseModel, root_validator
from starlette.authentication import AuthenticationError

from ralph.conf import settings

# Unused password used to avoid timing attacks, by comparing passwords supplied
# with invalid credentials to something innocuous with the same method as if
# it were a legitimate user.
UNUSED_PASSWORD = bcrypt.hashpw(b"ralph", bcrypt.gensalt())

security = HTTPBasic()

# API auth logger
logger = logging.getLogger(__name__)


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        username (str): Consists of the username of the current user.
        scopes (List): Consists of the scopes the user has access to.
    """

    username: str
    scopes: List[str]


class UserCredentials(AuthenticatedUser):
    """Pydantic model for user credentials as stored in the credentials file.

    Attributes:
        username (str): Consists of the username for a declared user.
        hash (str): Consists of the hashed password for a declared user.
        scopes (List): Consists of the scopes a declared has access to.
    """

    hash: str


class ServerUsersCredentials(BaseModel):
    """Custom root pydantic model.

    Describes expected list of all server users credentials as stored in
    the credentials file.

    Attributes:
        __root__ (List): Custom root consisting of the
                        list of all server users credentials.
    """

    __root__: List[UserCredentials]

    def __add__(self, other):  # noqa: D105
        return ServerUsersCredentials.parse_obj(self.__root__ + other.__root__)

    def __getitem__(self, item: int):  # noqa: D105
        return self.__root__[item]

    def __len__(self):  # noqa: D105
        return len(self.__root__)

    def __iter__(self):  # noqa: D105
        return iter(self.__root__)

    @root_validator
    @classmethod
    def ensure_unique_username(cls, values):
        """Every username should be unique among registered users."""
        usernames = [entry.username for entry in values.get("__root__")]
        if len(usernames) != len(set(usernames)):
            raise ValueError(
                "You cannot create multiple credentials with the same username"
            )
        return values


@lru_cache()
def get_stored_credentials(auth_file: Path) -> ServerUsersCredentials:
    """Helper to read the credentials/scopes file.

    Reads credentials from JSON file and stored them to avoid reloading them with every
    request.

    Args:
        auth_file (Path): Path to the JSON credentials scope file.

    Returns:
        credentials (ServerUsersCredentials): Cache-memorized credentials.

    """
    auth_file = Path(auth_file)
    if not auth_file.exists():
        msg = "Credentials file <%s> not found."
        logger.warning(msg, auth_file)
        raise AuthenticationError(msg.format(auth_file))
    return ServerUsersCredentials.parse_file(auth_file)

@lru_cache()
def _scope_is_authorized(requested_scope, user_scopes: Tuple):
    """Check if the requested scope can be accessed"""

    # List of all expanded scopes
    expanded_scopes = {
        'statements/read': {
            'statements/read/mine', 
            'statements/read'
        },
        'all/read': {
            'statements/read/mine', 
            'statements/read',
            'state/read', 
            'define', 
            'profile/read', 
            'all/read'
        },
        'all': {
            'statements/write', 
            'statements/read/mine', 
            'statements/read',
            'state/read', 
            'state/write', 
            'define', 
            'profile/read', 
            'profile/write', 
            'all/read', 
            'all'
        }
    }

    # Create a set with all the scopes available to the user
    expanded_user_scopes = set()
    for scope in user_scopes:
        expanded_user_scopes.update(expanded_scopes.get(scope, {scope}))
    
    return requested_scope in expanded_user_scopes


def authenticate_user(
        security_scopes: SecurityScopes,
        credentials: HTTPBasicCredentials = Depends(security)
    ):
    """Checks valid auth parameters.

    Gets the basic auth parameters from the Authorization header, and checks them
    against our own list of hashed credentials.

    Args:
        credentials (iterator): auth parameters from the Authorization header

    """
    try:
        user = next(
            filter(
                lambda u: u.username == credentials.username,
                get_stored_credentials(settings.AUTH_FILE),
            )
        )
        hashed_password = user.hash
    except StopIteration:
        # next() gets the first item in the enumerable; if there is none, it
        # raises a StopIteration error as it is out of bounds.
        logger.warning(
            "User %s tried to authenticate but this account does not exists",
            credentials.username,
        )
        hashed_password = None
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc

    if not hashed_password:
        # We're doing a bogus password check anyway to avoid timing attacks on
        # usernames
        bcrypt.checkpw(
            credentials.password.encode(settings.LOCALE_ENCODING), UNUSED_PASSWORD
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not bcrypt.checkpw(
        credentials.password.encode(settings.LOCALE_ENCODING),
        hashed_password.encode(settings.LOCALE_ENCODING),
    ):
        logger.warning(
            "Authentication failed for user %s",
            credentials.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    for requested_scope in security_scopes.scopes:
        if not _scope_is_authorized(requested_scope, tuple(user.scopes)):
            #print(f"Requested scope `{requested_scope}` is not authorized for this user ({user.scopes})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Access not authorized to scope: \"{requested_scope}\".",
                headers={"WWW-Authenticate": "Basic"},
            )

    return AuthenticatedUser(username=credentials.username, scopes=user.scopes)
 