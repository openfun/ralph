"""Basic authentication & authorization related tools for the Ralph API."""

import logging
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any, Iterator, List, Optional

import bcrypt
from cachetools import TTLCache, cached
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, root_validator
from starlette.authentication import AuthenticationError

from ralph.api.auth.user import AuthenticatedUser
from ralph.conf import settings

# Unused password used to avoid timing attacks, by comparing passwords supplied
# with invalid credentials to something innocuous with the same method as if
# it were a legitimate user.
UNUSED_PASSWORD = bcrypt.hashpw(b"ralph", bcrypt.gensalt())


security = HTTPBasic(auto_error=False)

# API auth logger
logger = logging.getLogger(__name__)


class UserCredentials(AuthenticatedUser):
    """Pydantic model for user credentials as stored in the credentials file.

    Attributes:
        hash (str): Consists of the hashed password for a declared user.
        username (str): Consists of the username for a declared user.
    """

    hash: str
    username: str


class ServerUsersCredentials(BaseModel):
    """Custom root pydantic model.

    Describe expected list of all server users credentials as stored in
    the credentials file.

    Attributes:
        __root__ (List): Custom root consisting of the
                        list of all server users credentials.
    """

    __root__: List[UserCredentials]

    def __add__(self, other) -> Any:  # noqa: D105
        return ServerUsersCredentials.parse_obj(self.__root__ + other.__root__)

    def __getitem__(self, item: int) -> UserCredentials:  # noqa: D105
        return self.__root__[item]

    def __len__(self) -> int:  # noqa: D105
        return len(self.__root__)

    def __iter__(self) -> Iterator[UserCredentials]:  # noqa: D105
        return iter(self.__root__)

    @root_validator
    @classmethod
    def ensure_unique_username(cls, values: Any) -> Any:
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

    Read credentials from JSON file and stored them to avoid reloading them with every
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


@cached(
    TTLCache(maxsize=settings.AUTH_CACHE_MAX_SIZE, ttl=settings.AUTH_CACHE_TTL),
    lock=Lock(),
    key=lambda credentials: (
        credentials.username,
        credentials.password,
    )
    if credentials is not None
    else None,
)
def get_basic_auth_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
) -> AuthenticatedUser:
    """Check valid auth parameters.

    Get the basic auth parameters from the Authorization header, and checks them
    against our own list of hashed credentials.

    Args:
        credentials (iterator): auth parameters from the Authorization header

    Raises:
        HTTPException
    """
    if not credentials:
        logger.debug("No credentials were found for Basic auth")
        return None

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

    # Check that a password was passed
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

    # Check password validity
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

    user = AuthenticatedUser(scopes=user.scopes, agent=dict(user.agent))

    return user
