"""Tests for ralph backends mixins"""

import json
import os.path

from ralph.backends.mixins import HistoryMixin
from ralph.defaults import APP_DIR, HISTORY_FILE


def test_backends_mixins_history_mixin_empty_history(fs):
    """Tests the history method of the HistoryMixin when history is empty."""
    # pylint: disable=unused-argument, invalid-name, protected-access

    history = HistoryMixin()

    # Property has not been cached yet.
    assert not hasattr(history, "_history")

    # History file or even the APP_DIR are not supposed to exist before trying
    # to access the history for the first time.
    assert not os.path.exists(str(APP_DIR))
    assert not os.path.exists(str(HISTORY_FILE))
    assert history.history == []

    # Even after trying to read the history for the first time, the file system
    # should stay pristine.
    assert not os.path.exists(str(APP_DIR))
    assert not os.path.exists(str(HISTORY_FILE))

    # Cached property should be effective now.
    assert hasattr(history, "_history")
    assert history._history == history.history


def test_backends_mixins_history_mixin_with_history(fs):
    """Tests the history method of the HistoryMixin when history is filled."""
    # pylint: disable=invalid-name

    history = HistoryMixin()

    # Add history events
    events = [{"event": "foo"}]
    fs.create_file(HISTORY_FILE, contents=json.dumps(events))

    assert history.history == events


def test_backends_mixins_history_mixin_write_history(fs):
    """Tests the write_history method of the HistoryMixin."""
    # pylint: disable=invalid-name, protected-access

    history = HistoryMixin()

    # History file or even the APP_DIR are not supposed to exist before trying
    # to write the history for the first time.
    assert not os.path.exists(str(APP_DIR))
    assert not os.path.exists(str(HISTORY_FILE))

    # Looks like pyfakefs needs some help with pathlib overrides (we are using
    # Path().parent in our implementation).
    fs.create_dir(str(APP_DIR))

    # Write history
    events = [{"event": "foo"}]
    history.write_history(events)
    assert os.path.exists(str(APP_DIR))
    assert os.path.exists(str(HISTORY_FILE))
    assert HISTORY_FILE.read_text() == json.dumps(events)
    assert history._history == events
    assert history.history == events


def test_backends_mixins_history_mixin_clean_history(fs):
    """Tests the clean_history method of the HistoryMixin."""
    # pylint: disable=invalid-name

    history = HistoryMixin()

    # Add history events
    events = [
        {"command": "foo"},
        {"command": "bar"},
        {"command": "foo"},
        {"command": "lol"},
        {"command": "bar"},
    ]
    fs.create_file(HISTORY_FILE, contents=json.dumps(events))

    history.clean_history(lambda event: event.get("command") == "foo")
    assert history.history == [
        {"command": "bar"},
        {"command": "lol"},
        {"command": "bar"},
    ]


def test_backends_mixins_history_mixin_append_to_history(fs):
    """Tests the append_to_history method of the HistoryMixin."""
    # pylint: disable=invalid-name, protected-access

    history = HistoryMixin()

    # Looks like pyfakefs needs some help with pathlib overrides (we are using
    # Path().parent in our implementation).
    fs.create_dir(str(APP_DIR))

    # Write history
    events = [{"event": "foo"}]
    history.write_history(events)

    # Append new event
    history.append_to_history({"event": "bar"})
    expected = [{"event": "foo"}, {"event": "bar"}]
    assert HISTORY_FILE.read_text() == json.dumps(expected)
    assert history._history == expected
    assert history.history == expected
