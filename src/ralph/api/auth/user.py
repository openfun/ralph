"""Authenticated user for the Ralph API."""

from typing import Dict, List

from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        agent (dict): The agent representing the current user.
        scopes (list): The scopes the user has access to.
    """

    agent: Dict
    scopes: List[str]
