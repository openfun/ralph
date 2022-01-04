"""
Main module for Ralph's LRS API.
"""
from fastapi import FastAPI, Request
from starlette.middleware.authentication import AuthenticationMiddleware

from .auth import BasicAuthBackend, on_auth_error

app = FastAPI()
app.add_middleware(
    AuthenticationMiddleware, backend=BasicAuthBackend(), on_error=on_auth_error
)


@app.get("/whoami")
async def whoami(request: Request):
    """
    Return the current user's username along with their scopes.
    """
    return {"username": request.user.username, "scopes": request.auth.scopes}
