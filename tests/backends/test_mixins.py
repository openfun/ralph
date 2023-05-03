"""Tests for ralph backends mixins."""

import json
import os.path
from pathlib import Path

from ralph.backends.mixins import HistoryEntry, HistoryMixin
from ralph.conf import Settings, settings
from ralph.utils import now


def test_backends_mixins_history_mixin_empty_history(settings_fs):
    """Tests the history method of the HistoryMixin when history is empty."""
    # pylint: disable=protected-access,unused-argument

    history = HistoryMixin()

    # Property has not been cached yet.
    assert not hasattr(history, "_history")

    # History file or even the APP_DIR are not supposed to exist before trying
    # to access the history for the first time.
    assert not os.path.exists(settings.APP_DIR)
    assert not os.path.exists(settings.HISTORY_FILE)
    assert history.history == []

    # Even after trying to read the history for the first time, the file system
    # should stay pristine.
    assert not os.path.exists(settings.APP_DIR)
    assert not os.path.exists(settings.HISTORY_FILE)

    # Cached property should be effective now.
    assert hasattr(history, "_history")
    assert history._history == history.history


def test_backends_mixins_history_mixin_with_history(fs, settings_fs):
    """Tests the history method of the HistoryMixin when history is filled."""
    # pylint: disable=invalid-name,unused-argument

    history = HistoryMixin()

    # Add history events
    events = [{"event": "foo"}]
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(events))

    assert history.history == events


def test_backends_mixins_history_mixin_write_history(fs, settings_fs):
    """Tests the write_history method of the HistoryMixin."""
    # pylint: disable=invalid-name, protected-access, unused-argument

    # Force Path instantiation with fake FS
    history_file_path = Path(settings.APP_DIR / "history.json")

    history = HistoryMixin()

    # History file or even the APP_DIR are not supposed to exist before trying
    # to write the history for the first time.
    assert not os.path.exists(settings.APP_DIR)
    assert not os.path.exists(settings.HISTORY_FILE)

    # Looks like pyfakefs needs some help with pathlib overrides (we are using
    # Path().parent in our implementation).
    fs.create_dir(str(settings.APP_DIR))

    # Write history
    events = [{"event": "foo"}]
    history.write_history(events)
    assert os.path.exists(settings.APP_DIR)
    assert os.path.exists(settings.HISTORY_FILE)
    assert Settings(HISTORY_FILE=history_file_path).HISTORY_FILE.read_text(
        encoding=settings.LOCALE_ENCODING
    ) == json.dumps(events)
    assert history._history == events
    assert history.history == events


def test_backends_mixins_history_mixin_clean_history(fs, settings_fs):
    """Tests the clean_history method of the HistoryMixin."""
    # pylint: disable=invalid-name,unused-argument

    history = HistoryMixin()

    # Add history events
    events = [
        {"action": "read"},
        {"action": "write"},
        {"action": "read"},
        {"action": "write"},
        {"action": "read"},
    ]
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(events))

    history.clean_history(lambda event: event.get("action") == "read")
    assert history.history == [
        {"action": "write"},
        {"action": "write"},
    ]


def test_backends_mixins_history_mixin_append_to_history(fs):
    """Tests the append_to_history method of the HistoryMixin."""
    # pylint: disable=invalid-name, protected-access

    history = HistoryMixin()

    # Looks like pyfakefs needs some help with pathlib overrides (we are using
    # Path().parent in our implementation).
    fs.create_dir(str(settings.APP_DIR))

    # Write history
    timestamp_foo = now()
    events = [
        {
            "backend": "foo",
            "action": "read",
            "id": "foo_id",
            "size": 3,
            "timestamp": timestamp_foo,
        }
    ]
    history.write_history(events)

    # Append new event
    timestamp_bar = now()
    history.append_to_history(
        {
            "backend": "bar",
            "action": "read",
            "id": "bar_id",
            "size": 3,
            "timestamp": timestamp_bar,
        }
    )
    expected = [
        {
            "backend": "foo",
            "action": "read",
            "id": "foo_id",
            "size": 3,
            "timestamp": timestamp_foo,
        },
        {
            "backend": "bar",
            "action": "read",
            "id": "bar_id",
            "size": 3,
            "timestamp": timestamp_bar,
        },
    ]
    assert settings.HISTORY_FILE.read_text(
        encoding=settings.LOCALE_ENCODING
    ) == json.dumps(expected)
    assert history._history == expected
    assert history.history == expected
