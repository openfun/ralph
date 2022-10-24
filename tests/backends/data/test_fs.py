"""Tests for Ralph fs storage backend"""

import json
import os
from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4

import pytest

from ralph.backends.data.base import BaseOperationType, BaseQuery, DataBackendStatus
from ralph.backends.data.fs import FileSystemDataBackend
from ralph.conf import settings
from ralph.exceptions import BackendParameterException


def test_backends_data_fs_file_system_data_backend_instantiation(fs):
    """Test the `FileSystemDataBackend` backend instantiation."""
    # pylint: disable=invalid-name,unused-argument

    assert FileSystemDataBackend.name == "fs"
    assert FileSystemDataBackend.query_model == BaseQuery
    assert FileSystemDataBackend.default_operation_type == BaseOperationType.CREATE

    backend = FileSystemDataBackend()

    assert backend.default_directory == Path(backend.settings.DEFAULT_DIRECTORY_PATH)
    assert backend.default_query_string == backend.settings.DEFAULT_QUERY_STRING
    assert backend.default_chunk_size == backend.settings.DEFAULT_CHUNK_SIZE

    deep_path = "deep/directories/path"
    assert not os.path.exists(deep_path)

    backend = FileSystemDataBackend(
        default_directory_path=deep_path,
        default_query_string="foo.txt",
        default_chunk_size=1,
    )
    assert os.path.exists(deep_path)
    assert backend.default_directory == Path(deep_path)
    assert backend.default_directory.is_dir()
    assert backend.default_query_string == "foo.txt"
    assert backend.default_chunk_size == 1

    # Check that a storage with the same path doesn't throw an exception
    FileSystemDataBackend(deep_path)


def test_backends_data_fs_file_system_data_backend_status_method(fs):
    """Test the `FileSystemDataBackend.status` method."""
    # pylint: disable=invalid-name

    fs.create_dir(settings.APP_DIR)
    valid_path = "valid/"
    backend = FileSystemDataBackend(valid_path)
    assert backend.status() == DataBackendStatus.OK

    invalid_path = "invalid/"
    fs.create_dir(invalid_path)
    os.chmod(invalid_path, 0o000)
    backend = FileSystemDataBackend(invalid_path)
    assert backend.status() == DataBackendStatus.ERROR


def test_backends_data_fs_file_system_data_backend_list_method(fs):
    """Test the `FileSystemDataBackend.list` method."""
    # pylint: disable=invalid-name

    fs.create_dir(settings.APP_DIR)

    path = "test_fs/"
    filename1 = "file1"
    filename2 = "file2"
    backend = FileSystemDataBackend(path)

    fs.create_file(path + filename1, contents="content")
    fs.create_file(path + filename2, contents="some more content")

    assert isinstance(backend.list(), Iterable)
    assert isinstance(backend.list(new=True), Iterable)
    assert isinstance(backend.list(details=True), Iterable)

    simple_list = list(backend.list())
    assert path + filename1 in simple_list
    assert path + filename2 in simple_list
    assert len(simple_list) == 2

    # Read filename1 so it's not new anymore
    list(backend.read(query=filename1))

    new_list = list(backend.list(new=True))
    assert path + filename1 not in new_list
    assert path + filename2 in new_list
    assert len(new_list) == 1

    details = list(backend.list(details=True))
    assert any(
        (detail["filename"] == filename1 and detail["size"] == 7) for detail in details
    )
    assert any(
        (detail["filename"] == filename2 and detail["size"] == 17) for detail in details
    )
    assert len(details) == 2


def test_backends_data_fs_file_system_data_backend_read_method_with_raw_ouput(fs):
    """Test the FileSystemDataBackend read method with `raw_output` set to `True`."""
    # pylint: disable=invalid-name

    fs.create_dir(settings.APP_DIR)
    absolute_path = "/tmp/test_fs/"
    filename1 = "file1.txt"
    filename2 = "file2.txt"
    backend = FileSystemDataBackend()
    file_in_default_directory = (
        backend.settings.DEFAULT_DIRECTORY_PATH + "/default_file.txt"
    )
    fs.create_file(absolute_path + filename1, contents="content")
    fs.create_file(absolute_path + filename2, contents="some more content")
    fs.create_file(file_in_default_directory, contents="default file content")

    # Given `raw_output` set to True, no `query` and no `target`,
    # the read method should read all files matching
    # f"{default_target}/{default_query_string}" = f"{APP_DIR}/archives/*"
    result = list(backend.read(raw_output=True))
    assert result == [b"default file content"]

    # Given `raw_output` set to True, no `query` and an absolute `target` path,
    # the `read` method should read all files matching
    # f"{target}/{default_query_string}" = "/tmp/test_fs/*".
    result = list(backend.read(raw_output=True, target=absolute_path))
    assert result == [b"content", b"some more content"]

    # Given `raw_output` set to True, a `chunk_size` and an absolute `target` path,
    # the `read` method should write the output in chunks of the specified `chunk_size`.
    result = list(backend.read(raw_output=True, target=absolute_path, chunk_size=4))
    assert result == [b"cont", b"ent", b"some", b" mor", b"e co", b"nten", b"t"]

    # Given `raw_output` set to True and a `query`,
    # the `read` method should only read the files that match the `query`.
    result = list(backend.read(raw_output=True, query="file1*", target=absolute_path))
    assert result == [b"content"]

    # Given `raw_output` set to True and a `query` that does not match any file,
    # the `read` method should not yield anything.
    result = list(backend.read(raw_output=True, query="file_not_found"))
    assert result == []  # pylint: disable=use-implicit-booleaness-not-comparison


def test_backends_data_fs_file_system_data_backend_read_method_without_raw_output(fs):
    """Test the FileSystemDataBackend read method with `raw_output` set to `False`."""
    # pylint: disable=invalid-name

    fs.create_dir(settings.APP_DIR)
    absolute_path = "/tmp/test_fs/"
    filename1 = "file1.txt"
    filename2 = "file2.txt"
    backend = FileSystemDataBackend()
    file_in_default_directory = (
        backend.settings.DEFAULT_DIRECTORY_PATH + "/default_file.txt"
    )

    valid_dictionary = {"valid_key": "valid_value"}
    valid_json = json.dumps(valid_dictionary)
    invalid_json = "invalid JSON"
    default_file_content = f"{valid_json}\n{invalid_json}\n{valid_json}"

    fs.create_file(absolute_path + filename1, contents="invalid content")
    fs.create_file(absolute_path + filename2, contents=valid_json)
    fs.create_file(file_in_default_directory, contents=default_file_content)

    # Given no `query` and no `target`
    # the `read` method should read all files matching
    # f"{default_target}/{default_query_string}" = f"{APP_DIR}/archives/*"
    result = list(backend.read())
    assert result == [valid_dictionary, valid_dictionary]

    # Given no `query` and an absolute `target` path,
    # the read method should read all files matching
    # f"{target}/{default_query_string}" = "/tmp/test_fs/*".
    result = list(backend.read(target=absolute_path))
    assert result == [valid_dictionary]

    # Given `raw_output` is set to `False` and a `chunk_size`,
    # the `read` method should ignore the `chunk_size` argument.
    result = list(backend.read(target=absolute_path, chunk_size=4))
    assert result == [valid_dictionary]

    # Given the query argument the read method should only read the files that match the
    # query.
    result = list(backend.read(query="file1*", target=absolute_path))
    assert result == []  # pylint: disable=use-implicit-booleaness-not-comparison

    # Given a `query` that does not match any file,
    # the `read` method should not yield anything.
    result = list(backend.read(query="file_not_found"))
    assert result == []  # pylint: disable=use-implicit-booleaness-not-comparison


@pytest.mark.parametrize(
    "operation_type", [None, BaseOperationType.CREATE, BaseOperationType.INDEX]
)
def test_backends_data_fs_file_system_data_backend_write_method_with_file_exists_error(
    operation_type, fs
):
    """Test the `FileSystemDataBackend.write` method, given a target matching an
    existing file and a `CREATE` or `INDEX` `operation_type`, should raise a
    `FileExistsError`.
    """
    # pylint: disable=invalid-name

    fs.create_file(settings.APP_DIR / "foo.txt", contents="content")
    backend = FileSystemDataBackend(str(settings.APP_DIR))
    msg = (
        f"{str(settings.APP_DIR)}/foo.txt already exists and overwrite is not allowed"
        " with operation_type create or index."
    )
    with pytest.raises(FileExistsError, match=msg):
        backend.write(target="foo.txt", stream=[b"foo"], operation_type=operation_type)


def test_backends_data_fs_file_system_data_backend_write_method_with_delete_operation(
    fs,
):
    """Test the `FileSystemDataBackend.write` method, given a `DELETE`
    `operation_type`, should raise a `BackendParameterException`.
    """
    # pylint: disable=invalid-name

    fs.create_dir(settings.APP_DIR)
    backend = FileSystemDataBackend()
    msg = "Delete operation_type is not allowed."
    with pytest.raises(BackendParameterException, match=msg):
        backend.write(stream=[b"foo"], operation_type=BaseOperationType.DELETE)


def test_backends_data_fs_file_system_data_backend_write_method_with_update_operation(
    fs,
):
    """Test the `FileSystemDataBackend.write` method, given an `UPDATE`
    `operation_type`, should overwrite the target file content with the content from the
    stream.
    """
    # pylint: disable=invalid-name,use-implicit-booleaness-not-comparison

    fs.create_file(settings.APP_DIR / "foo.txt", contents="content")
    backend = FileSystemDataBackend(str(settings.APP_DIR))
    kwargs = {"operation_type": BaseOperationType.UPDATE}

    # Overwriting foo.txt
    assert list(backend.read(query="foo.txt", raw_output=True)) == [b"content"]
    assert backend.write(stream=[b"bar"], target="foo.txt", **kwargs) == 1
    assert list(backend.read(query="foo.txt", raw_output=True)) == [b"bar"]

    # Clearing foo.txt
    assert backend.write(stream=[], target="foo.txt", **kwargs) == 1
    assert list(backend.read(query="foo.txt", raw_output=True)) == []

    # Creating bar.txt
    assert backend.write(stream=[b"baz"], target="bar.txt", **kwargs) == 1
    assert list(backend.read(query="bar.txt", raw_output=True)) == [b"baz"]


def test_backends_data_fs_file_system_data_backend_write_method_with_append_operation(
    fs,
):
    """Test the `FileSystemDataBackend.write` method, given an `APPEND`
    `operation_type`, should append the content from the stream to the end of the target
    file.
    """
    # pylint: disable=invalid-name,use-implicit-booleaness-not-comparison

    fs.create_file(settings.APP_DIR / "foo.txt", contents="foo")
    backend = FileSystemDataBackend(str(settings.APP_DIR))
    kwargs = {"operation_type": BaseOperationType.APPEND}

    # Overwriting foo.txt
    assert list(backend.read(query="foo.txt", raw_output=True)) == [b"foo"]
    assert backend.write(stream=[b"bar"], target="foo.txt", **kwargs) == 1
    assert list(backend.read(query="foo.txt", raw_output=True)) == [b"foobar"]


def test_backends_data_fs_file_system_data_backend_write_method_without_target(
    fs, monkeypatch
):
    """Test the `FileSystemDataBackend.write` method, given no `target` argument,
    should create a new random file and write the stream content into it.
    """
    # pylint: disable=invalid-name

    fs.create_dir(settings.APP_DIR)
    backend = FileSystemDataBackend(str(settings.APP_DIR))

    frozen_uuid4 = uuid4()
    frozen_uuid4_str = str(frozen_uuid4)
    monkeypatch.setattr("ralph.backends.data.fs.uuid4", lambda: frozen_uuid4)

    assert not os.path.exists(settings.APP_DIR / frozen_uuid4_str)
    assert backend.write(stream=[b"foo", b"bar"]) == 1
    assert os.path.exists(settings.APP_DIR / frozen_uuid4_str)
    assert list(backend.read(query=frozen_uuid4_str, raw_output=True)) == [b"foobar"]
