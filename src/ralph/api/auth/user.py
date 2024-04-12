"""Authenticated user for the Ralph API."""

from typing import FrozenSet, Literal, Optional

from pydantic import BaseModel, RootModel

from ralph.models.xapi.base.agents import BaseXapiAgent

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


class UserScopes(RootModel[FrozenSet[Scope]]):
    """Scopes available to users."""

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
        for scope in self.root:
            expanded_user_scopes.update(expanded_scopes.get(scope, {scope}))

        return requested_scope in expanded_user_scopes


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        agent (dict): The agent representing the current user.
        scopes (list): The scopes the user has access to.
        target (str or None): The target index or database to store statements into.
    """

    agent: BaseXapiAgent
    scopes: UserScopes
    target: Optional[str] = None
