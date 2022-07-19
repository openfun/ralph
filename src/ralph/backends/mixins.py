"""Backend mixins for Ralph"""

import json
import logging

from ralph.conf import settings

logger = logging.getLogger(__name__)


class HistoryMixin:
    """Handle backend download history to avoid fetching same files multiple
    times if they are already available."""

    @property
    def history(self):
        """Get backend history"""

        logging.debug("Loading history file: %s", str(settings.HISTORY_FILE))

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
        """Write given history as a JSON file"""

        logging.debug("Writing history file: %s", str(settings.HISTORY_FILE))

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
        """Append event to history"""

        self.write_history(self.history + [event])

    def get_command_history(self, backend_name, command):
        """Returns a set of entry ids from the history for a command and backend_name"""

        return [
            entry["id"]
            for entry in filter(
                lambda e: e["backend"] == backend_name and e["command"] == command,
                self.history,
            )
        ]
