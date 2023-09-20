"""Authenticated user for the Ralph API."""

from typing import Dict, List, Literal

from pydantic import BaseModel

Scope = Literal[
    "statements/write",
    "statements/read/mine",
    "statements/read",
    "state/write",
    "state/read",
    "define",
    "profile/write",
    "profile/read",
    "all/read",
    "all",
]


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        agent (dict): The agent representing the current user.
        scopes (list): The scopes the user has access to.
    """

    agent: Dict
    scopes: List[Scope]
