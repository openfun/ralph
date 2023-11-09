"""Backend mixins for Ralph."""

import json
import logging

from ralph.conf import settings

logger = logging.getLogger(__name__)


class HistoryMixin:
    """Backend history mixin.

    Handle backend download history to avoid fetching same files multiple
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

    def append_to_history(self, event):
        """Append event to history."""
        self.write_history(self.history + [event])

    def get_command_history(self, backend_name, command):
        """Extract entry ids from the history for a given command and backend_name."""

        def filter_by_name_and_command(entry):
            """Check whether the history entry matches the backend_name and command."""
            return entry.get("backend") == backend_name and (
                command in [entry.get("command"), entry.get("action")]
            )

        return [
            entry["id"] for entry in filter(filter_by_name_and_command, self.history)
        ]
