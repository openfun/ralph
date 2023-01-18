"""Tests for Ralph swift storage backend."""

import datetime
import json
import logging
import sys

import pytest
from swiftclient.service import SwiftService

from ralph.conf import settings
from ralph.exceptions import BackendException, BackendParameterException


def test_backends_storage_swift_storage_instantiation_failure_should_raise_exception(
    monkeypatch, swift, caplog
):
    """Checks that SwiftStorage raises BackendParameterException on failure."""
    error = "Unauthorized. Check username/id"

    def mock_failed_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": False, "error": error}

    monkeypatch.setattr(SwiftService, "stat", mock_failed_stat)
    caplog.set_level(logging.ERROR)

    with pytest.raises(BackendParameterException, match=error):
        swift()
    logger_name = "ralph.backends.storage.swift"
    msg = f"Unable to connect to the requested container: {error}"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]


def test_backends_storage_swift_storage_instantiation_should_not_raise_exception(
    monkeypatch, swift
):
    """Checks that SwiftStorage doesn't raise exceptions when the connection is
    successful.
    """

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    try:
        swift()
    except Exception:  # pylint:disable=broad-except
        pytest.fail("SwiftStorage should not raise exception on successful connection")


@pytest.mark.parametrize("pages_count", [1, 2])
def test_backends_storage_swift_list_should_yield_archive_names(
    pages_count, swift, monkeypatch, fs, settings_fs
):  # pylint:disable=invalid-name,unused-argument
    """Tests that given SwiftService.list method successfully connects to the Swift
    storage, the SwiftStorage list method should yield the archives.
    """
    listing = [
        {"name": "2020-04-29.gz"},
        {"name": "2020-04-30.gz"},
        {"name": "2020-05-01.gz"},
    ]
    history = [
        {"id": "2020-04-29.gz", "backend": "swift", "command": "fetch"},
        {"id": "2020-04-30.gz", "backend": "swift", "command": "fetch"},
    ]

    def mock_list_with_pages(*args, **kwargs):  # pylint:disable=unused-argument
        return [{"success": True, "listing": listing}] * pages_count

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    monkeypatch.setattr(SwiftService, "list", mock_list_with_pages)
    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))
    swift = swift()
    assert list(swift.list()) == [x["name"] for x in listing] * pages_count
    assert list(swift.list(new=True)) == ["2020-05-01.gz"] * pages_count
    assert list(swift.list(details=True)) == listing * pages_count


@pytest.mark.parametrize("pages_count", [1, 2])
def test_backends_storage_swift_list_with_failed_connection_should_log_the_error(
    pages_count, swift, monkeypatch, fs, caplog, settings_fs
):  # pylint:disable=invalid-name,unused-argument,too-many-arguments
    """Tests that given SwiftService.list method fails to retrieve the list of archives,
    the SwiftStorage list method should log the error and raise a BackendException.
    """

    def mock_list_with_pages(*args, **kwargs):  # pylint:disable=unused-argument
        return [
            {
                "success": False,
                "container": "ralph_logs_container",
                "error": "Container not found",
            }
        ] * pages_count

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    monkeypatch.setattr(SwiftService, "list", mock_list_with_pages)
    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))
    caplog.set_level(logging.ERROR)
    swift = swift()
    msg = "Failed to list container ralph_logs_container: Container not found"
    with pytest.raises(BackendException, match=msg):
        next(swift.list())
    with pytest.raises(BackendException, match=msg):
        next(swift.list(new=True))
    with pytest.raises(BackendException, match=msg):
        next(swift.list(details=True))
    logger_name = "ralph.backends.storage.swift"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)] * 3


def test_backends_storage_swift_read_with_valid_name_should_write_to_history(
    swift, monkeypatch, fs, settings_fs
):  # pylint:disable=invalid-name,unused-argument
    """Tests that given SwiftService.download method successfully retrieves from the
    Swift storage the object with the provided name (the object exists),
    the SwiftStorage read method should write the entry to the history.
    """

    def mock_successful_download(*args, **kwargs):  # pylint:disable=unused-argument
        yield {"contents": [b"some", b"contents"]}

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    freezed_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    monkeypatch.setattr(SwiftService, "download", mock_successful_download)
    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    monkeypatch.setattr("ralph.backends.storage.swift.now", lambda: freezed_now)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))

    swift = swift()
    list(swift.read("2020-04-29.gz"))
    assert swift.history == [
        {
            "backend": "swift",
            "command": "fetch",
            "id": "2020-04-29.gz",
            "size": 12,
            "fetched_at": freezed_now,
        }
    ]


def test_backends_storage_swift_read_with_invalid_name_should_log_the_error(
    swift, monkeypatch, fs, caplog, settings_fs
):  # pylint:disable=invalid-name,unused-argument
    """Tests that given SwiftService.download method fails to retrieve from the Swift
    storage the object with the provided name (the object does not exists on Swift),
    the SwiftStorage read method should log the error, not write to history and raise a
    BackendException.
    """
    error = "ClientException Object GET failed"

    def mock_failed_download(*args, **kwargs):  # pylint:disable=unused-argument
        yield {"object": "2020-04-31.gz", "error": error}

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    monkeypatch.setattr(SwiftService, "download", mock_failed_download)
    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))
    caplog.set_level(logging.ERROR)

    swift = swift()
    msg = f"Failed to download 2020-04-31.gz: {error}"
    with pytest.raises(BackendException, match=msg):
        list(swift.read("2020-04-31.gz"))
    logger_name = "ralph.backends.storage.swift"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]
    assert swift.history == []


# pylint: disable=line-too-long
@pytest.mark.parametrize("overwrite", [False, True])
@pytest.mark.parametrize("new_archive", [False, True])
def test_backends_storage_swift_write_should_write_to_history_new_or_overwriten_archives(  # noqa
    overwrite, new_archive, swift, monkeypatch, fs, caplog, settings_fs
):  # pylint:disable=invalid-name, too-many-arguments, too-many-locals,unused-argument
    """Tests that given SwiftService list/upload method successfully connects to the
    Swift storage, the SwiftStorage write method should update the history file when
    overwrite is True or when the name of the archive is not in the history.
    In case overwrite is False and the archive is in the history, the write method
    should raise a FileExistsError.
    """
    history = [
        {"id": "2020-04-29.gz", "backend": "swift", "command": "fetch"},
        {"id": "2020-04-30.gz", "backend": "swift", "command": "fetch"},
    ]
    listing = [
        {"name": "2020-04-29.gz"},
        {"name": "2020-04-30.gz"},
        {"name": "2020-05-01.gz"},
    ]
    freezed_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    archive_name = "not_in_history.gz" if new_archive else "2020-04-29.gz"
    new_history_entry = [
        {
            "backend": "swift",
            "command": "push",
            "id": archive_name,
            "pushed_at": freezed_now,
        }
    ]

    def mock_successful_upload(*args, **kwargs):  # pylint:disable=unused-argument
        yield {"success": True}

    def mock_successful_list(*args, **kwargs):  # pylint:disable=unused-argument
        return [{"success": True, "listing": listing}]

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    monkeypatch.setattr(SwiftService, "upload", mock_successful_upload)
    monkeypatch.setattr(SwiftService, "list", mock_successful_list)
    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    monkeypatch.setattr("ralph.backends.storage.swift.now", lambda: freezed_now)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))
    caplog.set_level(logging.ERROR)

    swift = swift()
    if not overwrite and not new_archive:
        new_history_entry = []
        msg = f"{archive_name} already exists and overwrite is not allowed"
        with pytest.raises(FileExistsError, match=msg):
            swift.write(sys.stdin.buffer, archive_name, overwrite=overwrite)
        logger_name = "ralph.backends.storage.swift"
        assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]
    else:
        swift.write(sys.stdin.buffer, archive_name, overwrite=overwrite)
    assert swift.history == history + new_history_entry


def test_backends_storage_swift_write_should_log_the_error(
    swift, monkeypatch, fs, caplog, settings_fs
):  # pylint:disable=invalid-name,unused-argument
    """Tests that given SwiftService.upload method fails to write the archive,
    the SwiftStorage write method should log the error, raise a BackendException
    and not write to history.
    """
    error = "Unauthorized. Check username/id, password"
    history = [
        {"id": "2020-04-29.gz", "backend": "swift", "command": "fetch"},
        {"id": "2020-04-30.gz", "backend": "swift", "command": "fetch"},
    ]
    listing = [
        {"name": "2020-04-29.gz"},
        {"name": "2020-04-30.gz"},
        {"name": "2020-05-01.gz"},
    ]

    def mock_failed_upload(*args, **kwargs):  # pylint:disable=unused-argument
        yield {"success": False, "error": error}

    def mock_successful_list(*args, **kwargs):  # pylint:disable=unused-argument
        return [{"success": True, "listing": listing}]

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    monkeypatch.setattr(SwiftService, "upload", mock_failed_upload)
    monkeypatch.setattr(SwiftService, "list", mock_successful_list)
    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))
    caplog.set_level(logging.ERROR)

    swift = swift()
    with pytest.raises(BackendException, match=error):
        swift.write(sys.stdin.buffer, "2020-04-29.gz", overwrite=True)
    logger_name = "ralph.backends.storage.swift"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, error)]
    assert swift.history == history


def test_backends_storage_url_should_concatenate_the_storage_url_and_name(
    swift, monkeypatch
):
    """Checks the url method returns `os_storage_url/name`."""

    def mock_successful_stat(*args, **kwargs):  # pylint:disable=unused-argument
        return {"success": True}

    monkeypatch.setattr(SwiftService, "stat", mock_successful_stat)
    assert swift().url("name") == "os_storage_url/name"
