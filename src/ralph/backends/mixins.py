"""Backend mixins for Ralph"""

import json
import logging

from ralph.defaults import HISTORY_FILE

logger = logging.getLogger(__name__)


class HistoryMixin:
    """Handle backend download history to avoid fetching same files multiple
    times if they are already available."""

    @property
    def history(self):
        """Get backend history"""

        logging.debug("Loading history file: %s", str(HISTORY_FILE))

        if not hasattr(self, "_history"):
            try:
                with HISTORY_FILE.open() as history_file:
                    self._history = json.load(history_file)
            except FileNotFoundError:
                self._history = []
        return self._history

    # pylint: disable=no-self-use
    def write_history(self, history):
        """Write given history as a JSON file"""

        logging.debug("Writing history file: %s", str(HISTORY_FILE))

        if not HISTORY_FILE.parent.exists():
            HISTORY_FILE.parent.mkdir(parents=True)

        with HISTORY_FILE.open("w") as history_file:
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
