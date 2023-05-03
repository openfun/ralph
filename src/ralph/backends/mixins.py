"""Backend mixins for Ralph."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from fastapi.encoders import jsonable_encoder

from ralph.backends.data.base import BaseOperationType
from ralph.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """Class for a history entry."""

    backend: str
    action: Literal["read", "write"]
    id: str
    size: int
    timestamp: datetime
    operation_type: Optional[BaseOperationType] = None


class HistoryMixin:
    """Backend history mixin.

    Handles backend download history to avoid fetching same files multiple
    times if they are already available.
    """

    @property
    def history(self):
        """Get backend history."""
        logger.debug("Loading history file: %s", str(settings.HISTORY_FILE))

        if not hasattr(self, "_history"):
            try:
                with settings.HISTORY_FILE.open(
                    encoding=settings.LOCALE_ENCODING
                ) as history_file:
                    self._history = json.load(history_file)
            except FileNotFoundError:
                self._history = []
        return self._history

    # pylint: disable=no-self-use
    def write_history(self, history):
        """Write given history as a JSON file."""
        logger.debug("Writing history file: %s", str(settings.HISTORY_FILE))

        if not settings.HISTORY_FILE.parent.exists():
            settings.HISTORY_FILE.parent.mkdir(parents=True)

        with settings.HISTORY_FILE.open(
            "w", encoding=settings.LOCALE_ENCODING
        ) as history_file:
            json.dump(history, history_file)

        # Update history
        self._history = history

    def clean_history(self, selector):
        """Clean selected events from the history.

        selector: a callable that selects events that need to be removed
        """
        self._history = list(filter(lambda event: not selector(event), self.history))
        self.write_history(self._history)

    def append_to_history(self, event: HistoryEntry):
        """Append event to history."""
        self.write_history(self.history + [jsonable_encoder(event, exclude_unset=True)])

    def get_command_history(self, backend_name, command):
        """Extracts entry ids from the history for a given command and backend_name."""

        def filter_by_name_and_command(entry):
            """Checks whether the history entry matches the backend_name and command."""
            return entry.get("backend") == backend_name and (
                command in entry.get("action")
            )

        return [
            entry["id"] for entry in filter(filter_by_name_and_command, self.history)
        ]
