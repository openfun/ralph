"""Authenticated user for the Ralph API."""

from functools import lru_cache
from typing import Dict, FrozenSet, Literal

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


class UserScopes(FrozenSet[Scope]):
    @lru_cache()
    def is_authorized(self, requested_scope: Scope):
        """Check if the requested scope can be accessed based on user scopes."""

        expanded_scopes = {
            "statements/read": {"statements/read/mine", "statements/read"},
            "all/read": {
                "statements/read/mine",
                "statements/read",
                "state/read",
                "profile/read",
                "all/read",
            },
            "all": {
                "statements/write",
                "statements/read/mine",
                "statements/read",
                "state/read",
                "state/write",
                "define",
                "profile/read",
                "profile/write",
                "all/read",
                "all",
            },
        }

        expanded_user_scopes = set()
        for scope in self:
            expanded_user_scopes.update(expanded_scopes.get(scope, {scope}))

        return requested_scope in expanded_user_scopes


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        agent (dict): The agent representing the current user.
        scopes (list): The scopes the user has access to.
    """

    agent: Dict
    scopes: UserScopes
