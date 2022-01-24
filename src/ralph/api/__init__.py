"""
Main module for Ralph's LRS API.
"""
from fastapi import Depends, FastAPI

from .auth import AuthenticatedUser, authenticated_user

app = FastAPI()


@app.get("/whoami")
async def whoami(user: AuthenticatedUser = Depends(authenticated_user)):
    """
    Return the current user's username along with their scopes.
    """
    return {"username": user.username, "scopes": user.scopes}
