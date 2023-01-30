"""Authenticated user for the Ralph API."""

from typing import List, Optional

from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    """Pydantic model for user authentication.

    Attributes:
        username (str): Consists of the username of the current user.
        scopes (list): Consists of the scopes the user has access to.
    """

    username: str
    scopes: Optional[List[str]]
