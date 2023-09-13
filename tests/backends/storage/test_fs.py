"""Tests for Ralph fs storage backend."""

from collections.abc import Iterable
from pathlib import Path

import pytest

from ralph.backends.storage.fs import FSStorage
from ralph.conf import settings


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_backends_storage_fs_storage_instantiation(fs):
    """Test the FSStorage backend instantiation."""
    # pylint: disable=protected-access

    assert FSStorage.name == "fs"

    storage = FSStorage()

    assert str(storage._path) == settings.BACKENDS.STORAGE.FS.PATH

    deep_path = "deep/directories/path"

    storage = FSStorage(deep_path)

    assert storage._path == Path(deep_path)
    assert storage._path.is_dir()

    # Check that a storage with the same path doesn't throw an exception
    FSStorage(deep_path)


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_backends_storage_fs_getfile(fs):
    """Test that an existing path can be returned, and throws an exception
    otherwise.
    """
    # pylint: disable=protected-access

    path = "test_fs/"
    filename = "some_file"
    storage = FSStorage(path)

    storage._get_filepath(filename)
    with pytest.raises(FileNotFoundError):
        storage._get_filepath(filename, strict=True)
    storage._get_filepath(filename, strict=False)

    fs.create_file(Path(path, filename))

    assert storage._get_filepath(filename, strict=True) == Path(path, filename)


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_backends_storage_fs_url(fs):
    """Test that the full URL of the file can be returned."""
    path = "test_fs/"
    filename = "some_file"
    storage = FSStorage(path)

    fs.create_file(Path(path, filename))

    assert storage.url(filename) == "/test_fs/some_file"


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_backends_storage_fs_list(fs, settings_fs):
    """Test archives listing in FSStorage."""
    fs.create_dir(settings.APP_DIR)

    path = "test_fs/"
    filename1 = "file1"
    filename2 = "file2"
    storage = FSStorage(path)

    fs.create_file(path + filename1, contents="content")
    fs.create_file(path + filename2, contents="some more content")

    assert isinstance(storage.list(), Iterable)
    assert isinstance(storage.list(new=True), Iterable)
    assert isinstance(storage.list(details=True), Iterable)

    simple_list = list(storage.list())
    assert filename1 in simple_list
    assert filename2 in simple_list
    assert len(simple_list) == 2

    # Fetch it so it's not new anymore
    list(storage.read(filename1))

    new_list = list(storage.list(new=True))
    assert filename1 not in new_list
    assert filename2 in new_list
    assert len(new_list) == 1

    detail_list = list(storage.list(details=True))
    assert any(
        (archive["filename"] == filename1 and archive["size"] == 7)
        for archive in detail_list
    )
    assert any(
        (archive["filename"] == filename2 and archive["size"] == 17)
        for archive in detail_list
    )
    assert len(simple_list) == 2
