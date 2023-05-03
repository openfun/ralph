"""Tests for Ralph fs data backend"""
import json
import logging
import os
from collections.abc import Iterable
from operator import itemgetter
from uuid import uuid4

import pytest

from ralph.backends.data.base import BaseOperationType, BaseQuery, DataBackendStatus
from ralph.backends.data.fs import FSDataBackend, FSDataBackendSettings
from ralph.backends.mixins import HistoryEntry
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now


def test_backends_data_fs_data_backend_default_instantiation(monkeypatch, fs):
    """Tests the `FSDataBackend` default instantiation."""
    # pylint: disable=invalid-name
    fs.create_file(".env")
    backend_settings_names = [
        "DEFAULT_CHUNK_SIZE",
        "DEFAULT_DIRECTORY_PATH",
        "DEFAULT_QUERY_STRING",
        "LOCALE_ENCODING",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__FS__{name}", raising=False)

    assert FSDataBackend.name == "fs"
    assert FSDataBackend.query_model == BaseQuery
    assert FSDataBackend.default_operation_type == BaseOperationType.CREATE
    assert FSDataBackend.settings_class == FSDataBackendSettings
    backend = FSDataBackend()
    assert str(backend.default_directory) == "."
    assert backend.default_query_string == "*"
    assert backend.default_chunk_size == 4096
    assert backend.locale_encoding == "utf8"


def test_backends_data_fs_data_backend_instantiation_with_settings(fs):
    """Tests the `FSDataBackend` instantiation with settings."""
    # pylint: disable=invalid-name,unused-argument
    deep_path = "deep/directories/path"
    assert not os.path.exists(deep_path)
    settings = FSDataBackend.settings_class(
        DEFAULT_DIRECTORY_PATH=deep_path,
        DEFAULT_QUERY_STRING="foo.txt",
        DEFAULT_CHUNK_SIZE=1,
        LOCALE_ENCODING="utf-16",
    )
    backend = FSDataBackend(settings)
    assert os.path.exists(deep_path)
    assert str(backend.default_directory) == deep_path
    assert backend.default_directory.is_dir()
    assert backend.default_query_string == "foo.txt"
    assert backend.default_chunk_size == 1
    assert backend.locale_encoding == "utf-16"

    try:
        FSDataBackend(settings)
    except Exception as err:  # pylint:disable=broad-except
        pytest.fail(f"FSDataBackend should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "mode",
    [0o007, 0o100, 0o200, 0o300, 0o400, 0o500, 0o600],
)
def test_backends_data_fs_data_backend_status_method_with_error_status(
    mode, fs_backend, caplog
):
    """Tests the `FSDataBackend.status` method, given a directory with wrong
    permissions, should return `DataBackendStatus.ERROR`.
    """
    os.mkdir("directory", mode)
    with caplog.at_level(logging.ERROR):
        assert fs_backend(path="directory").status() == DataBackendStatus.ERROR

    assert (
        "ralph.backends.data.fs",
        logging.ERROR,
        "Invalid permissions for the default directory at /directory. "
        "The directory should have read, write and execute permissions.",
    ) in caplog.record_tuples


@pytest.mark.parametrize("mode", [0o700])
def test_backends_data_fs_data_backend_status_method_with_ok_status(mode, fs_backend):
    """Tests the `FSDataBackend.status` method, given a directory with right
    permissions, should return `DataBackendStatus.OK`.
    """
    os.mkdir("directory", mode)
    assert fs_backend(path="directory").status() == DataBackendStatus.OK


@pytest.mark.parametrize(
    "files,target,error",
    [
        # Given a `target` that is a file, the `list` method should raise a
        # `BackendParameterException`.
        (["foo/file_1"], "file_1", "Invalid target argument', 'Not a directory"),
        # Given a `target` that does not exists, the `list` method should raise a
        # `BackendParameterException`.
        (["foo/file_1"], "bar", "Invalid target argument', 'No such file or directory"),
    ],
)
def test_backends_data_fs_data_backend_list_method_with_invalid_target(
    files, target, error, fs_backend, fs
):
    """Tests the `FSDataBackend.list` method given an invalid `target` argument should
    raise a `BackendParameterException`.
    """
    # pylint: disable=invalid-name
    for file in files:
        fs.create_file(file)

    backend = fs_backend()
    with pytest.raises(BackendParameterException, match=error):
        list(backend.list(target))


@pytest.mark.parametrize(
    "files,target,expected",
    [
        # Given an empty default directory, the `list` method should yield nothing.
        ([], None, []),
        # Given a default directory containing one file, the `list` method should yield
        # the absolute path of the file.
        (["foo/file_1"], None, ["/foo/file_1"]),
        # Given a relative `target` directory containing one file, the `list` method
        # should yield the absolute path of the file.
        (["/foo/bar/file_1"], "bar", ["/foo/bar/file_1"]),
        # Given a default directory containing two files, the `list` method should yield
        # the absolute paths of the files.
        (["foo/file_1", "foo/file_2"], None, ["/foo/file_1", "/foo/file_2"]),
        # Given a `target` directory containing two files, the `list` method should
        # yield the absolute paths of the files.
        (["bar/file_1", "bar/file_2"], "/bar", ["/bar/file_1", "/bar/file_2"]),
    ],
)
def test_backends_data_fs_data_backend_list_method_without_history(
    files, target, expected, fs_backend, fs
):
    """Tests the `FSDataBackend.list` method without history."""
    # pylint: disable=invalid-name
    for file in files:
        fs.create_file(file)

    backend = fs_backend()
    result = backend.list(target)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected


@pytest.mark.parametrize(
    "files,target,expected",
    [
        # Given an empty default directory, the `list` method should yield nothing.
        ([], None, []),
        # Given a default directory containing one file, the `list` method should yield
        # a dictionary containing the absolute path of the file.
        (["foo/file_1"], None, ["/foo/file_1"]),
        # Given a relative `target` directory containing one file, the `list` method
        # should yield a dictionary containing the absolute path of the file.
        (["/foo/bar/file_1"], "bar", ["/foo/bar/file_1"]),
        # Given a default directory containing two files, the `list` method should yield
        # dictionaries containing the absolute paths of the files.
        (["foo/file_1", "foo/file_2"], None, ["/foo/file_1", "/foo/file_2"]),
        # Given a `target` directory containing two files, the `list` method should
        # yield dictionaries containing the absolute paths of the files.
        (["bar/file_1", "bar/file_2"], "/bar", ["/bar/file_1", "/bar/file_2"]),
    ],
)
def test_backends_data_fs_data_backend_list_method_with_details(
    files, target, expected, fs_backend, fs
):
    """Tests the `FSDataBackend.list` method with `details` set to `True`."""
    # pylint: disable=invalid-name,too-many-arguments
    for file in files:
        fs.create_file(file)
        os.utime(file, (1, 1))

    backend = fs_backend()
    result = backend.list(target, details=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("path")) == [
        {"path": file, "size": 0, "modified_at": "1970-01-01T00:00:01+00:00"}
        for file in expected
    ]


def test_backends_data_fs_data_backend_list_method_with_history(fs_backend, fs):
    """Tests the `FSDataBackend.list` method with history."""
    # pylint: disable=invalid-name

    # Create 3 files in the default directory.
    fs.create_file("foo/file_1")
    fs.create_file("foo/file_2")
    fs.create_file("foo/file_3")

    backend = fs_backend()

    # Given an empty history and `new` set to `True`, the `list` method should yield all
    # files in the directory.
    expected = ["/foo/file_1", "/foo/file_2", "/foo/file_3"]
    result = backend.list(new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected

    # Add file_1 to history
    backend.history.append(
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_1",
            "size": 0,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # Given a history containing one matching file and `new` set to `True`, the
    # `list` method should yield all files in the directory except the matching file.
    expected = ["/foo/file_2", "/foo/file_3"]
    result = backend.list(new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected

    # Add file_2 to history
    backend.history.append(
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_2",
            "size": 0,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # Given a history containing two matching files and `new` set to `True`, the
    # `list` method should yield all files in the directory except the matching files.
    expected = ["/foo/file_3"]
    result = backend.list(new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected

    # Add file_3 to history
    backend.history.append(
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_3",
            "size": 0,
            "timestamp": "2020-10-07T16:37:25.887664+00:00",
        }
    )

    # Given a history containing all matching files and `new` set to `True`, the `list`
    # method should yield nothing.
    expected = []
    result = backend.list(new=True)
    assert isinstance(result, Iterable)
    assert sorted(result) == expected


def test_backends_data_fs_data_backend_list_method_with_history_and_details(
    fs_backend, fs
):
    """Tests the `FSDataBackend.list` method with an history and detailed output."""
    # pylint: disable=invalid-name

    # Create 3 files in the default directory.
    fs.create_file("foo/file_1")
    os.utime("foo/file_1", (1, 1))
    fs.create_file("foo/file_2")
    os.utime("foo/file_2", (1, 1))
    fs.create_file("foo/file_3")
    os.utime("foo/file_3", (1, 1))

    backend = fs_backend()

    # Given an empty history and `new` and `details` set to `True`, the `list` method
    # should yield all files in the directory with additional details.
    expected = [
        {"path": file, "size": 0, "modified_at": "1970-01-01T00:00:01+00:00"}
        for file in ["/foo/file_1", "/foo/file_2", "/foo/file_3"]
    ]
    result = backend.list(details=True, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("path")) == expected

    # Add file_1 to history
    backend.history.append(
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_1",
            "size": 0,
            "timestamp": "1970-01-01T00:00:01+00:00",
        }
    )

    # Given a history containing one matching file and `new` and `details` set to
    # `True`, the `list` method should yield all files in the directory with additional
    # details, except for the matching file.
    expected = [
        {"path": file, "size": 0, "modified_at": "1970-01-01T00:00:01+00:00"}
        for file in ["/foo/file_2", "/foo/file_3"]
    ]
    result = backend.list(details=True, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("path")) == expected

    # Add file_2 to history
    backend.history.append(
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_2",
            "size": 0,
            "timestamp": "1970-01-01T00:00:01+00:00",
        }
    )

    # Given a history containing two matching files and `new` and `details` set to
    # `True`, the `list` method should yield all files in the directory with additional
    # details, except for the matching files.
    expected = [
        {"path": file, "size": 0, "modified_at": "1970-01-01T00:00:01+00:00"}
        for file in ["/foo/file_3"]
    ]
    result = backend.list(details=True, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("path")) == expected

    # Add file_3 to history
    backend.history.append(
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_3",
            "size": 0,
            "timestamp": "1970-01-01T00:00:01+00:00",
        }
    )

    # Given a history containing all matching files and `new` and `details` set to
    # `True`, the `list` method should yield nothing.
    expected = []
    result = backend.list(details=True, new=True)
    assert isinstance(result, Iterable)
    assert sorted(result, key=itemgetter("path")) == expected


def test_backends_data_fs_data_backend_read_method_with_raw_ouput(
    fs_backend, fs, monkeypatch
):
    """Tests the `FSDataBackend.read` method with `raw_output` set to `True`."""
    # pylint: disable=invalid-name

    # Create files in absolute path directory.
    absolute_path = "/tmp/test_fs/"
    fs.create_file(absolute_path + "file_1.txt", contents="foo")
    fs.create_file(absolute_path + "file_2.txt", contents="bar")

    # Create files in default directory.
    fs.create_file("foo/file_3.txt", contents="baz")
    fs.create_file("foo/bar/file_4.txt", contents="qux")

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.fs.now", lambda: frozen_now)

    backend = fs_backend()

    # Given no `target`, the `read` method should read all files in the default
    # directory and yield bytes.
    result = backend.read(raw_output=True)
    assert isinstance(result, Iterable)
    assert list(result) == [b"baz"]

    # When the `read` method is called successfully, then a new entry should be added to
    # the history.
    assert backend.history == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_3.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        }
    ]

    # Given an absolute `target` path, the `read` method should read all files in the
    # target directory and yield bytes.
    result = backend.read(raw_output=True, target=absolute_path)
    assert isinstance(result, Iterable)
    assert list(result) == [b"foo", b"bar"]

    # When the `read` method is called successfully, then a new entry should be added to
    # the history.
    assert backend.history[-2:] == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/tmp/test_fs/file_1.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        },
        {
            "backend": "fs",
            "action": "read",
            "id": "/tmp/test_fs/file_2.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        },
    ]

    # Given a relative `target` path, the `read` method should read all files in the
    # target directory relative to the default directory and yield bytes.
    result = backend.read(raw_output=True, target="./bar")
    assert isinstance(result, Iterable)
    assert list(result) == [b"qux"]

    # When the `read` method is called successfully, then a new entry should be added to
    # the history.
    assert backend.history[-1:] == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/bar/file_4.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        }
    ]

    # Given a `chunk_size` and an absolute `target` path,
    # the `read` method should write the output bytes in chunks of the specified
    # `chunk_size`.
    result = backend.read(raw_output=True, target=absolute_path, chunk_size=2)
    assert isinstance(result, Iterable)
    assert list(result) == [b"fo", b"o", b"ba", b"r"]

    # When the `read` method is called successfully, then a new entry should be added to
    # the history.
    assert backend.history[-2:] == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/tmp/test_fs/file_1.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        },
        {
            "backend": "fs",
            "action": "read",
            "id": "/tmp/test_fs/file_2.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        },
    ]


def test_backends_data_fs_data_backend_read_method_without_raw_output(
    fs_backend, fs, monkeypatch
):
    """Tests the `FSDataBackend.read` method with `raw_output` set to `False`."""
    # pylint: disable=invalid-name

    # File contents.
    valid_dictionary = {"foo": "bar"}
    valid_json = json.dumps(valid_dictionary)

    # Create files in absolute path directory.
    absolute_path = "/tmp/test_fs/"
    fs.create_file(absolute_path + "file_1.txt", contents=valid_json)

    # Create files in default directory.
    fs.create_file("foo/file_2.txt", contents=f"{valid_json}\n{valid_json}")
    fs.create_file(
        "foo/bar/file_3.txt", contents=f"{valid_json}\n{valid_json}\n{valid_json}"
    )

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.fs.now", lambda: frozen_now)

    backend = fs_backend()

    # Given no `target`, the `read` method should read all files in the default
    # directory and yield dictionaries.
    result = backend.read(raw_output=False)
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary, valid_dictionary]

    # When the `read` method is called successfully, then a new entry should be added to
    # the history.
    assert backend.history == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/file_2.txt",
            "size": 29,
            "timestamp": frozen_now,
            "operation_type": None,
        }
    ]

    # Given an absolute `target` path, the `read` method should read all files in the
    # target directory and yield dictionaries.
    result = backend.read(raw_output=False, target=absolute_path)
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary]

    # When the `read` method is called successfully, then a new entry should be added to
    # the history.
    assert backend.history[-1:] == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/tmp/test_fs/file_1.txt",
            "size": 14,
            "timestamp": frozen_now,
            "operation_type": None,
        }
    ]

    # Given a relative `target` path, the `read` method should read all files in the
    # target directory relative to the default directory and yield dictionaries.
    result = backend.read(raw_output=False, target="bar")
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary, valid_dictionary, valid_dictionary]

    # When the `read` method is called successfully, then a new entry should be added to
    # the history.
    assert backend.history[-1:] == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/bar/file_3.txt",
            "size": 44,
            "timestamp": frozen_now,
            "operation_type": None,
        }
    ]


def test_backends_data_fs_data_backend_read_method_with_ignore_errors(fs_backend, fs):
    """Tests the `FSDataBackend.read` method with `ignore_errors` set to `True`, given
    a file containing invalid JSON lines, should skip the invalid lines.
    """
    # pylint: disable=invalid-name

    # File contents.
    valid_dictionary = {"foo": "bar"}
    valid_json = json.dumps(valid_dictionary)
    invalid_json = "baz"
    valid_invalid_json = f"{valid_json}\n{invalid_json}\n{valid_json}"
    invalid_valid_jdon = f"{invalid_json}\n{valid_json}\n{invalid_json}"

    # Create files in absolute path directory.
    absolute_path = "/tmp/test_fs/"
    fs.create_file(absolute_path + "file_1.txt", contents=valid_json)
    fs.create_file(absolute_path + "file_2.txt", contents=invalid_json)

    # Create files in default directory.
    fs.create_file("foo/file_3.txt", contents=valid_invalid_json)
    fs.create_file("foo/bar/file_4.txt", contents=invalid_valid_jdon)

    backend = fs_backend()

    # Given no `target`, the `read` method should read all files in the default
    # directory and yield dictionaries.
    result = backend.read(ignore_errors=True)
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary, valid_dictionary]

    # Given an absolute `target` path, the `read` method should read all files in the
    # target directory and yield dictionaries.
    result = backend.read(ignore_errors=True, target=absolute_path)
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary]

    # Given a relative `target` path, the `read` method should read all files in the
    # target directory relative to the default directory and yield dictionaries.
    result = backend.read(ignore_errors=True, target="bar")
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary]


def test_backends_data_fs_data_backend_read_method_without_ignore_errors(
    fs_backend, fs, monkeypatch
):
    """Tests the `FSDataBackend.read` method with `ignore_errors` set to `False`, given
    a file containing invalid JSON lines, should raise a `BackendException`.
    """
    # pylint: disable=invalid-name

    # File contents.
    valid_dictionary = {"foo": "bar"}
    valid_json = json.dumps(valid_dictionary)
    invalid_json = "baz"
    valid_invalid_json = f"{valid_json}\n{invalid_json}\n{valid_json}"
    invalid_valid_jdon = f"{invalid_json}\n{valid_json}\n{invalid_json}"

    # Create files in absolute path directory.
    absolute_path = "/tmp/test_fs/"
    fs.create_file(absolute_path + "file_1.txt", contents=valid_json)
    fs.create_file(absolute_path + "file_2.txt", contents=invalid_json)

    # Create files in default directory.
    fs.create_file("foo/file_3.txt", contents=valid_invalid_json)
    fs.create_file("foo/bar/file_4.txt", contents=invalid_valid_jdon)

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.fs.now", lambda: frozen_now)

    backend = fs_backend()

    # Given no `target`, the `read` method should read all files in the default
    # directory.
    # Given one file in the default directory with an invalid json at the second line,
    # the `read` method should yield the first valid line and raise a `BackendException`
    # at the second line.
    result = backend.read(ignore_errors=False)
    assert isinstance(result, Iterable)
    assert next(result) == valid_dictionary
    with pytest.raises(BackendException, match="Raised error:"):
        next(result)

    # When the `read` method fails to read a file entirely, then no entry should be
    # added to the history.
    assert not backend.history

    # Given an absolute `target` path, the `read` method should read all files in the
    # target directory.
    # Given two files in the target directory, the first containing valid json and the
    # second containing invalid json, the `read` method should yield the content of the
    # first valid file and raise a `BackendException` when reading the invalid file.
    result = backend.read(ignore_errors=False, target=absolute_path)
    assert isinstance(result, Iterable)
    assert next(result) == valid_dictionary
    with pytest.raises(BackendException, match="Raised error:"):
        next(result)

    # When the `read` method succeeds to read one file entirely, and fails to read
    # another file, then a new entry for the succeeded file should be added to the
    # history.
    assert backend.history == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/tmp/test_fs/file_1.txt",
            "size": 14,
            "timestamp": frozen_now,
            "operation_type": None,
        }
    ]

    # Given a relative `target` path, the `read` method should read all files in the
    # target directory relative to the default directory.
    # Given one file in the relative target directory with an invalid json at the first
    # line, the `read` method should raise a `BackendException`.
    result = backend.read(ignore_errors=False, target="bar")
    assert isinstance(result, Iterable)
    with pytest.raises(BackendException, match="Raised error:"):
        next(result)

    # When the `read` method fails to read a file entirely, then no new entry should be
    # added to the history.
    assert len(backend.history) == 1


def test_backends_data_fs_data_backend_read_method_with_query(fs_backend, fs):
    """Tests the `FSDataBackend.read` method, given a query argument."""
    # pylint: disable=invalid-name

    # File contents.
    valid_dictionary = {"foo": "bar"}
    valid_json = json.dumps(valid_dictionary)
    invalid_json = "invalid JSON"

    # Create files in absolute path directory.
    absolute_path = "/tmp/test_fs/"
    fs.create_file(absolute_path + "file_1.txt", contents=invalid_json)
    fs.create_file(absolute_path + "file_2.txt", contents=valid_json)

    # Create files in default directory.
    default_path = "foo/"
    fs.create_file(default_path + "file_3.txt", contents=valid_json)
    fs.create_file(default_path + "file_4.txt", contents=valid_json)
    fs.create_file(default_path + "/bar/file_5.txt", contents=invalid_json)

    backend = fs_backend()

    # Given a `query` and no `target`, the `read` method should only read the files that
    # match the query in the default directory and yield dictionaries.
    result = backend.read(query="file_*")
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary, valid_dictionary]

    # Given a `query` and an absolute `target`, the `read` method should only read the
    # files that match the query and yield dictionaries.
    result = backend.read(query="file_2*", target=absolute_path)
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary]

    # Given a `query`, no `target` and `raw_output` set to `True`, the `read` method
    # should only read the files that match the query in the default directory and yield
    # bytes.
    result = backend.read(query="*file*", raw_output=True)
    assert isinstance(result, Iterable)
    assert list(result) == [valid_json.encode(), valid_json.encode()]
    # A relative query should behave in the same way.
    result = backend.read(query="bar/file_*", raw_output=True)
    assert isinstance(result, Iterable)
    assert list(result) == [invalid_json.encode()]

    # Given a `query` that does not match any file, the `read` method should not yield
    # anything.
    result = backend.read(query="file_not_found")
    assert isinstance(result, Iterable)
    assert not list(result)


@pytest.mark.parametrize(
    "operation_type", [None, BaseOperationType.CREATE, BaseOperationType.INDEX]
)
def test_backends_data_fs_data_backend_write_method_with_file_exists_error(
    operation_type, fs_backend, fs
):
    """Tests the `FSDataBackend.write` method, given a target matching an
    existing file and a `CREATE` or `INDEX` `operation_type`, should raise a
    `BackendException`.
    """
    # pylint: disable=invalid-name

    # Create files in default directory.
    fs.create_file("foo/foo.txt", contents="content")

    backend = fs_backend()

    msg = (
        "foo.txt already exists and overwrite is not allowed with operation_type create"
        " or index."
    )
    with pytest.raises(BackendException, match=msg):
        backend.write(target="foo.txt", data=[b"foo"], operation_type=operation_type)

    # When the `write` method fails, then no entry should be added to the history.
    assert not sorted(backend.history, key=itemgetter("id"))


def test_backends_data_fs_data_backend_write_method_with_delete_operation(
    fs_backend,
):
    """Tests the `FSDataBackend.write` method, given a `DELETE` `operation_type`, should
    raise a `BackendParameterException`.
    """
    # pylint: disable=invalid-name
    backend = fs_backend()

    msg = "Delete operation_type is not allowed."
    with pytest.raises(BackendParameterException, match=msg):
        backend.write(data=[b"foo"], operation_type=BaseOperationType.DELETE)

    # When the `write` method fails, then no entry should be added to the history.
    assert not sorted(backend.history, key=itemgetter("id"))


def test_backends_data_fs_data_backend_write_method_with_update_operation(
    fs_backend, fs, monkeypatch
):
    """Tests the `FSDataBackend.write` method, given an `UPDATE` `operation_type`,
    should overwrite the target file content with the provided data.
    """
    # pylint: disable=invalid-name

    # Create files in default directory.
    fs.create_file("foo/foo.txt", contents="content")

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.fs.now", lambda: frozen_now)

    backend = fs_backend()
    kwargs = {"operation_type": BaseOperationType.UPDATE}

    # Overwriting foo.txt.
    assert list(backend.read(query="foo.txt", raw_output=True)) == [b"content"]
    assert backend.write(data=[b"bar"], target="foo.txt", **kwargs) == 1

    # When the `write` method is called successfully, then a new entry should be added
    # to the history.
    assert backend.history == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/foo.txt",
            "size": 7,
            "timestamp": frozen_now,
            "operation_type": None,
        },
        {
            "backend": "fs",
            "action": "write",
            "id": "/foo/foo.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": BaseOperationType.UPDATE.value,
        },
    ]
    assert list(backend.read(query="foo.txt", raw_output=True)) == [b"bar"]

    # Clearing foo.txt.
    assert backend.write(data=[b""], target="foo.txt", **kwargs) == 1
    assert not list(backend.read(query="foo.txt", raw_output=True))

    # When the `write` method is called successfully, then a new entry should be added
    # to the history.
    assert backend.history[-2:] == [
        {
            "backend": "fs",
            "action": "write",
            "id": "/foo/foo.txt",
            "size": 0,
            "timestamp": frozen_now,
            "operation_type": BaseOperationType.UPDATE.value,
        },
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/foo.txt",
            "size": 0,
            "timestamp": frozen_now,
            "operation_type": None,
        },
    ]

    # Creating bar.txt.
    assert backend.write(data=[b"baz"], target="bar.txt", **kwargs) == 1
    assert list(backend.read(query="bar.txt", raw_output=True)) == [b"baz"]

    # When the `write` method is called successfully, then a new entry should be added
    # to the history.
    assert backend.history[-2:] == [
        {
            "backend": "fs",
            "action": "write",
            "id": "/foo/bar.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": BaseOperationType.UPDATE.value,
        },
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/bar.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        },
    ]


@pytest.mark.parametrize(
    "data,expected",
    [
        ([b"bar"], [b"foobar"]),
        ([b"bar", b"baz"], [b"foobarbaz"]),
        ((b"bar" for _ in range(1)), [b"foobar"]),
        ((b"bar" for _ in range(3)), [b"foobarbarbar"]),
        (
            [{}, {"foo": [1, 2, 4], "bar": {"baz": None}}],
            [b'foo{}\n{"foo": [1, 2, 4], "bar": {"baz": null}}\n'],
        ),
    ],
)
def test_backends_data_fs_data_backend_write_method_with_append_operation(
    data, expected, fs_backend, fs, monkeypatch
):
    """Tests the `FSDataBackend.write` method, given an `APPEND` `operation_type`,
    should append the provided data to the end of the target file.
    """
    # pylint: disable=invalid-name

    # Create files in default directory.
    fs.create_file("foo/foo.txt", contents="foo")

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.fs.now", lambda: frozen_now)

    backend = fs_backend()
    kwargs = {"operation_type": BaseOperationType.APPEND}

    # Overwriting foo.txt.
    assert list(backend.read(query="foo.txt", raw_output=True)) == [b"foo"]
    assert backend.write(data=data, target="foo.txt", **kwargs) == 1
    assert list(backend.read(query="foo.txt", raw_output=True)) == expected

    # When the `write` method is called successfully, then a new entry should be added
    # to the history.
    assert backend.history == [
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/foo.txt",
            "size": 3,
            "timestamp": frozen_now,
            "operation_type": None,
        },
        {
            "backend": "fs",
            "action": "write",
            "id": "/foo/foo.txt",
            "size": len(expected[0]),
            "timestamp": frozen_now,
            "operation_type": BaseOperationType.APPEND.value,
        },
        {
            "backend": "fs",
            "action": "read",
            "id": "/foo/foo.txt",
            "size": len(expected[0]),
            "timestamp": frozen_now,
            "operation_type": None,
        },
    ]


def test_backends_data_fs_data_backend_write_method_without_target(
    fs_backend, monkeypatch
):
    """Tests the `FSDataBackend.write` method, given no `target` argument,
    should create a new random file and write the provided data into it.
    """
    # pylint: disable=invalid-name

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.fs.now", lambda: frozen_now)

    # Freeze the uuid4() value.
    frozen_uuid4 = uuid4()
    monkeypatch.setattr("ralph.backends.data.fs.uuid4", lambda: frozen_uuid4)

    backend = fs_backend(path=".")

    expected_filename = f"{frozen_now}-{frozen_uuid4}"
    assert not os.path.exists(expected_filename)
    assert backend.write(data=[b"foo", b"bar"]) == 1
    assert os.path.exists(expected_filename)
    assert list(backend.read(query=expected_filename, raw_output=True)) == [b"foobar"]

    # When the `write` method is called successfully, then a new entry should be added
    # to the history.
    assert backend.history == [
        {
            "backend": "fs",
            "action": "write",
            "id": f"/{expected_filename}",
            "size": 6,
            "timestamp": frozen_now,
            "operation_type": BaseOperationType.CREATE.value,
        },
        {
            "backend": "fs",
            "action": "read",
            "id": f"/{expected_filename}",
            "size": 6,
            "timestamp": frozen_now,
            "operation_type": None,
        },
    ]
