"""Routers related tools for the Ralph API."""

from typing import Union

from ralph.backends.database.base import BaseAsyncDatabase, BaseDatabase
from ralph.conf import settings

# pylint: disable=invalid-name
DATABASE_CLIENT: Union[BaseDatabase, BaseAsyncDatabase] = getattr(
    settings.BACKENDS.DATABASE, settings.RUNSERVER_BACKEND.upper()
).get_instance()
