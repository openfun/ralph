"""Authenticated user for the Ralph API."""

from enum import Enum
from typing import Dict, List, Literal

from pydantic import BaseModel


class Scopes(str, Enum):
    """Authorized scopes to be associated with user accounts."""

    STATEMENTS_WRITE = "statements/write"
    STATEMENTS_READ_MINE = "statements/read/mine"
    STATEMENTS_READ = "statements/read"
    STATE = "state"
    DEFINE = "define"
    PROFILE_WRITE = "profile/write"
    PROFILE_READ_MINE = "profile/read/mine"
    PROFILE_READ = "profile/read"
    ALL_READ = "all/read"
    ALL = "all"


Scope = Literal[
    Scopes.STATEMENTS_WRITE,
    Scopes.STATEMENTS_READ_MINE,
    Scopes.STATEMENTS_READ,
    Scopes.STATE,
    Scopes.DEFINE,
    Scopes.PROFILE_WRITE,
    Scopes.PROFILE_READ_MINE,
    Scopes.PROFILE_READ,
    Scopes.ALL_READ,
    Scopes.ALL,
]


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        agent (dict): The agent representing the current user.
        scopes (list): The scopes the user has access to.
    """

    agent: Dict
    scopes: List[Scope]
