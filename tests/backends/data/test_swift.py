"""Tests for Ralph swift data backend."""

import json
import logging
import re
from io import BytesIO
from operator import itemgetter
from typing import Iterable
from uuid import uuid4

import pytest
from swiftclient.service import ClientException

from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.swift import (
    SwiftDataBackend,
    SwiftDataBackendSettings,
)
from ralph.conf import settings
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now


def test_backends_data_swift_default_instantiation(monkeypatch, fs):
    """Test the `SwiftDataBackend` default instantiation."""

    fs.create_file(".env")
    backend_settings_names = [
        "AUTH_URL",
        "USERNAME",
        "PASSWORD",
        "IDENTITY_API_VERSION",
        "TENANT_ID",
        "TENANT_NAME",
        "PROJECT_DOMAIN_NAME",
        "REGION_NAME",
        "OBJECT_STORAGE_URL",
        "USER_DOMAIN_NAME",
        "DEFAULT_CONTAINER",
        "LOCALE_ENCODING",
        "READ_CHUNK_SIZE",
        "WRITE_CHUNK_SIZE",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__SWIFT__{name}", raising=False)

    assert SwiftDataBackend.name == "swift"
    assert SwiftDataBackend.query_class == str
    assert SwiftDataBackend.default_operation_type == BaseOperationType.CREATE
    assert SwiftDataBackend.settings_class == SwiftDataBackendSettings
    backend = SwiftDataBackend()
    assert backend.options["tenant_id"] is None
    assert backend.options["tenant_name"] is None
    assert backend.options["project_domain_name"] == "Default"
    assert backend.options["region_name"] is None
    assert backend.options["object_storage_url"] is None
    assert backend.options["user_domain_name"] == "Default"
    assert backend.default_container is None
    assert backend.locale_encoding == "utf8"
    assert backend.settings.READ_CHUNK_SIZE == 4096
    assert backend.settings.WRITE_CHUNK_SIZE == 4096

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__SWIFT__DEFAULT_CONTAINER", "foo")
    backend = SwiftDataBackend()
    assert backend.default_container == "foo"
    backend.close()


def test_backends_data_swift_instantiation_with_settings(fs):
    """Test the `SwiftDataBackend` instantiation with settings."""

    fs.create_file(".env")
    settings_ = SwiftDataBackend.settings_class(
        AUTH_URL="https://toto.net/",
        USERNAME="username",
        PASSWORD="password",
        IDENTITY_API_VERSION="2",
        TENANT_ID="tenant_id",
        TENANT_NAME="tenant_name",
        PROJECT_DOMAIN_NAME="project_domain_name",
        REGION_NAME="region_name",
        OBJECT_STORAGE_URL="object_storage_url",
        USER_DOMAIN_NAME="user_domain_name",
        DEFAULT_CONTAINER="default_container",
        LOCALE_ENCODING="utf-16",
        READ_CHUNK_SIZE=300,
        WRITE_CHUNK_SIZE=299,
    )
    backend = SwiftDataBackend(settings_)
    assert backend.options["tenant_id"] == "tenant_id"
    assert backend.options["tenant_name"] == "tenant_name"
    assert backend.options["project_domain_name"] == "project_domain_name"
    assert backend.options["region_name"] == "region_name"
    assert backend.options["object_storage_url"] == "object_storage_url"
    assert backend.options["user_domain_name"] == "user_domain_name"
    assert backend.default_container == "default_container"
    assert backend.locale_encoding == "utf-16"
    assert backend.settings.READ_CHUNK_SIZE == 300
    assert backend.settings.WRITE_CHUNK_SIZE == 299

    try:
        SwiftDataBackend(settings_)
    except Exception as err:  # noqa: BLE001
        pytest.fail(f"Two SwiftDataBackends should not raise exceptions: {err}")
    backend.close()


def test_backends_data_swift_status_with_error_status(
    monkeypatch, swift_backend, caplog
):
    """Test the `SwiftDataBackend.status` method, given a failed connection,
    should return `DataBackendStatus.ERROR`."""
    error = (
        "Unauthorized. Check username/id, password, tenant name/id and"
        " user/tenant domain name/id."
    )

    def mock_failed_head_account(*args, **kwargs):
        raise ClientException(error)

    backend = swift_backend()
    monkeypatch.setattr(backend.connection, "head_account", mock_failed_head_account)

    with caplog.at_level(logging.ERROR):
        assert backend.status() == DataBackendStatus.ERROR

    assert (
        "ralph.backends.data.swift",
        logging.ERROR,
        f"Unable to connect to the Swift account: {error}",
    ) in caplog.record_tuples
    backend.close()


def test_backends_data_swift_status_with_ok_status(monkeypatch, swift_backend, caplog):
    """Test the `SwiftDataBackend.status` method, given a directory with wrong
    permissions, should return `DataBackendStatus.OK`.
    """

    def mock_successful_head_account(*args, **kwargs):
        return 1

    backend = swift_backend()
    monkeypatch.setattr(
        backend.connection, "head_account", mock_successful_head_account
    )

    with caplog.at_level(logging.ERROR):
        assert backend.status() == DataBackendStatus.OK

    assert caplog.record_tuples == []
    backend.close()


def test_backends_data_swift_list(swift_backend, monkeypatch, fs, settings_fs):
    """Test that the `SwiftDataBackend.list` method argument should list
    the default container.
    """
    frozen_now = now()
    listing = [
        {
            "name": "2020-04-29.gz",
            "lastModified": frozen_now,
            "size": 12,
        },
        {
            "name": "2020-04-30.gz",
            "lastModified": frozen_now,
            "size": 25,
        },
        {
            "name": "2020-05-01.gz",
            "lastModified": frozen_now,
            "size": 42,
        },
    ]
    history = [
        {
            "backend": "swift",
            "action": "read",
            "id": "2020-04-29.gz",
        },
        {
            "backend": "swift",
            "action": "read",
            "id": "2020-04-30.gz",
        },
    ]

    def mock_get_container(*args, **kwargs):
        return (None, [x["name"] for x in listing])

    def mock_head_object(container, obj):
        resp = next((x for x in listing if x["name"] == obj), None)
        return {
            "last-modified": resp["lastModified"],
            "content-length": resp["size"],
        }

    backend = swift_backend()
    monkeypatch.setattr(backend.connection, "get_container", mock_get_container)
    monkeypatch.setattr(backend.connection, "head_object", mock_head_object)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))

    assert list(backend.list()) == [x["name"] for x in listing]
    assert list(backend.list(new=True)) == ["2020-05-01.gz"]
    assert list(backend.list(details=True)) == listing
    backend.close()


def test_backends_data_swift_list_with_failed_details(
    swift_backend, monkeypatch, fs, caplog, settings_fs
):
    """Test that the `SwiftDataBackend.list` method with a failed connection
    when retrieving details, should log the error and raise a BackendException.
    """
    error = "Test client exception"

    frozen_now = now()
    listing = [
        {
            "name": "2020-04-29.gz",
            "last-modified": frozen_now,
            "size": 12,
        },
    ]

    def mock_get_container(*args, **kwargs):
        return (None, [x["name"] for x in listing])

    def mock_head_object(*args, **kwargs):
        raise ClientException(error)

    backend = swift_backend()
    monkeypatch.setattr(backend.connection, "get_container", mock_get_container)
    monkeypatch.setattr(backend.connection, "head_object", mock_head_object)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))

    error = "Test client exception"
    msg = f"Unable to retrieve details for object {listing[0]['name']}: {error}"

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            next(backend.list(details=True))

    assert ("ralph.backends.data.swift", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_swift_list_with_failed_connection(
    swift_backend, monkeypatch, fs, caplog, settings_fs
):
    """Test that the `SwiftDataBackend.list` method with a failed connection
    should log the error and raise a BackendException.
    """
    error = "Container not found"

    def mock_get_container(*args, **kwargs):
        raise ClientException(error)

    backend = swift_backend()
    monkeypatch.setattr(backend.connection, "get_container", mock_get_container)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))

    msg = "Failed to list container container_name: Container not found"

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            next(backend.list())
        with pytest.raises(BackendException, match=msg):
            next(backend.list(new=True))
        with pytest.raises(BackendException, match=msg):
            next(backend.list(details=True))

    assert ("ralph.backends.data.swift", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


def test_backends_data_swift_read_with_raw_output(
    swift_backend, monkeypatch, fs, settings_fs
):
    """Test the `SwiftDataBackend.read` method with `raw_output` set to `True`."""

    # Object contents.
    content = b'{"foo": "bar"}'

    # Freeze the ralph.utils.now() value.
    frozen_now = now()

    backend = swift_backend()

    def mock_get_object(*args, **kwargs):
        resp_headers = {"content-length": 14}
        return (resp_headers, BytesIO(content))

    monkeypatch.setattr(backend.connection, "get_object", mock_get_object)
    monkeypatch.setattr("ralph.backends.data.swift.now", lambda: frozen_now)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))

    # The `read` method should read the object and yield bytes.
    result = backend.read(raw_output=True, query="2020-04-29.gz")
    assert isinstance(result, Iterable)
    assert list(result) == [content]

    assert backend.history == [
        {
            "backend": "swift",
            "action": "read",
            "id": "container_name/2020-04-29.gz",
            "size": 14,
            "timestamp": frozen_now,
        }
    ]

    # Given a `chunk_size`,` the `read` method should write the output bytes
    # in chunks of the specified `chunk_size`.
    result = backend.read(raw_output=True, query="2020-05-30.gz", chunk_size=2)
    assert isinstance(result, Iterable)
    assert list(result) == [b'{"', b"fo", b'o"', b": ", b'"b', b"ar", b'"}']

    assert backend.history == [
        {
            "backend": "swift",
            "action": "read",
            "id": "container_name/2020-04-29.gz",
            "size": 14,
            "timestamp": frozen_now,
        },
        {
            "backend": "swift",
            "action": "read",
            "id": "container_name/2020-05-30.gz",
            "size": 14,
            "timestamp": frozen_now,
        },
    ]
    backend.close()


def test_backends_data_swift_read_without_raw_output(
    swift_backend, monkeypatch, fs, settings_fs
):
    """Test the `SwiftDataBackend.read` method with `raw_output` set to `False`."""

    # Object contents.
    content_dict = {"foo": "bar"}
    content_bytes = b'{"foo": "bar"}'

    # Freeze the ralph.utils.now() value.
    frozen_now = now()

    backend = swift_backend()

    def mock_get_object(*args, **kwargs):
        resp_headers = {"content-length": 14}
        return (resp_headers, BytesIO(content_bytes))

    monkeypatch.setattr(backend.connection, "get_object", mock_get_object)
    monkeypatch.setattr("ralph.backends.data.swift.now", lambda: frozen_now)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))

    # The `read` method should read the object and yield bytes.
    result = backend.read(raw_output=False, query="2020-04-29.gz")
    assert isinstance(result, Iterable)
    assert list(result) == [content_dict]

    assert backend.history == [
        {
            "backend": "swift",
            "action": "read",
            "id": "container_name/2020-04-29.gz",
            "size": 14,
            "timestamp": frozen_now,
        }
    ]
    backend.close()


def test_backends_data_swift_read_with_invalid_query(swift_backend, caplog):
    """Test the `SwiftDataBackend.read` method given an invalid `query` argument should
    raise a `BackendParameterException`.
    """
    backend = swift_backend(container=None)
    # Given no target `container` name, the `read` method should raise a
    # `BackendParameterException`.
    msg = "The target container is not set"
    with pytest.raises(BackendParameterException, match=re.escape(msg)):
        with caplog.at_level(logging.ERROR):
            list(backend.read())

    assert ("ralph.backends.data.swift", logging.ERROR, msg) in caplog.record_tuples

    # Given no object `query`, the `read` method should raise a
    # `BackendParameterException`.
    msg = "The object query is not set"
    with pytest.raises(BackendParameterException, match=re.escape(msg)):
        with caplog.at_level(logging.ERROR):
            list(backend.read(target="container_name"))

    assert ("ralph.backends.data.swift", logging.ERROR, msg) in caplog.record_tuples

    backend.close()


def test_backends_data_swift_read_with_ignore_errors(
    monkeypatch, swift_backend, fs, settings_fs
):
    """Test the `SwiftDataBackend.read` method with `ignore_errors` set to `True`,
    given an archive containing invalid JSON lines, should skip the invalid lines.
    """

    # File contents.
    valid_dictionary = {"foo": "bar"}
    valid_json = json.dumps(valid_dictionary)
    invalid_json = "baz"
    valid_invalid_json = bytes(
        f"{valid_json}\n{invalid_json}\n{valid_json}",
        encoding="utf8",
    )
    invalid_valid_json = bytes(
        f"{invalid_json}\n{valid_json}\n{invalid_json}",
        encoding="utf8",
    )

    backend = swift_backend()

    def mock_get_object_1(*args, **kwargs):
        resp_headers = {"content-length": 14}
        return (resp_headers, BytesIO(valid_invalid_json))

    monkeypatch.setattr(backend.connection, "get_object", mock_get_object_1)

    # The `read` method should read all valid statements and yield dictionaries
    result = backend.read(ignore_errors=True, query="2020-06-02.gz")
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary, valid_dictionary]

    def mock_get_object_2(*args, **kwargs):
        resp_headers = {"content-length": 14}
        return (resp_headers, BytesIO(invalid_valid_json))

    monkeypatch.setattr(backend.connection, "get_object", mock_get_object_2)

    # The `read` method should read all valid statements and yield bytes
    result = backend.read(ignore_errors=True, query="2020-06-02.gz")
    assert isinstance(result, Iterable)
    assert list(result) == [valid_dictionary]
    backend.close()


def test_backends_data_swift_read_without_ignore_errors(
    monkeypatch, swift_backend, fs, settings_fs
):
    """Test the `SwiftDataBackend.read` method with `ignore_errors` set to `False`,
    given a file containing invalid JSON lines, should raise a `BackendException`.
    """

    # File contents.
    valid_dictionary = {"foo": "bar"}
    valid_json = json.dumps(valid_dictionary)
    invalid_json = "baz"
    valid_invalid_json = bytes(
        f"{valid_json}\n{invalid_json}\n{valid_json}",
        encoding="utf8",
    )
    invalid_valid_json = bytes(
        f"{invalid_json}\n{valid_json}\n{invalid_json}",
        encoding="utf8",
    )

    backend = swift_backend()

    def mock_get_object_1(*args, **kwargs):
        resp_headers = {"content-length": 14}
        return (resp_headers, BytesIO(valid_invalid_json))

    monkeypatch.setattr(backend.connection, "get_object", mock_get_object_1)

    # Given one object with an invalid json at the second line, the `read`
    # method should yield the first valid line and raise a `BackendException`
    # at the second line.
    result = backend.read(ignore_errors=False, query="2020-06-02.gz")
    assert isinstance(result, Iterable)
    assert next(result) == valid_dictionary
    msg = (
        r"Failed to decode JSON: Expecting value: line 1 column 1 \(char 0\), "
        r"for document: b'baz\\n', at line 1"
    )
    with pytest.raises(BackendException, match=msg):
        next(result)

    # When the `read` method fails to read a file entirely, then no entry should be
    # added to the history.
    assert not backend.history

    def mock_get_object_2(*args, **kwargs):
        resp_headers = {"content-length": 14}
        return (resp_headers, BytesIO(invalid_valid_json))

    monkeypatch.setattr(backend.connection, "get_object", mock_get_object_2)

    # Given one object with an invalid json at the first and third lines, the `read`
    # method should raise a `BackendException` at the second line.
    result = backend.read(ignore_errors=False, query="2020-06-03.gz")
    assert isinstance(result, Iterable)
    msg = (
        r"Failed to decode JSON: Expecting value: line 1 column 1 \(char 0\), "
        r"for document: b'baz\\n', at line 0"
    )
    with pytest.raises(BackendException, match=msg):
        next(result)
    backend.close()


def test_backends_data_swift_read_with_failed_connection(
    caplog, monkeypatch, swift_backend
):
    """Test the `SwiftDataBackend.read` method, given a `ClientException` raised by
    method `get_object`, should raise a  `BackendException`."""

    error = "Failed to get object."

    def mock_failed_get_object(*args, **kwargs):
        raise ClientException(error)

    backend = swift_backend()
    monkeypatch.setattr(backend.connection, "get_object", mock_failed_get_object)

    msg = f"Failed to read object.gz: {error}"
    with caplog.at_level(logging.ERROR):
        result = backend.read(query="object.gz")
        with pytest.raises(BackendException, match=msg):
            next(result)

    assert ("ralph.backends.data.swift", logging.ERROR, msg) in caplog.record_tuples
    backend.close()


@pytest.mark.parametrize(
    "operation_type", [None, BaseOperationType.CREATE, BaseOperationType.INDEX]
)
def test_backends_data_swift_write_with_file_exists_error(
    operation_type, swift_backend, monkeypatch, fs, settings_fs
):
    """Test the `SwiftDataBackend.write` method, given a target matching an
    existing file and a `CREATE` or `INDEX` `operation_type`, should raise a
    `BackendException`.
    """

    listing = [{"name": "2020-04-29.gz"}, {"name": "object.gz"}]

    def mock_get_container(*args, **kwargs):
        return (None, [x["name"] for x in listing])

    backend = swift_backend()
    monkeypatch.setattr(backend.connection, "get_container", mock_get_container)

    msg = (
        f"object.gz already exists and overwrite is not allowed for operation"
        f" {operation_type if operation_type is not None else BaseOperationType.CREATE}"
    )

    with pytest.raises(BackendException, match=msg):
        backend.write(
            target="object.gz", data=[b"foo", b"test"], operation_type=operation_type
        )

    # When the `write` method fails, then no entry should be added to the history.
    assert not sorted(backend.history, key=itemgetter("id"))
    backend.close()


def test_backends_data_swift_write_with_failed_connection(
    monkeypatch, swift_backend, fs, settings_fs
):
    """Test the `SwiftDataBackend.write` method, given a failed connection, should
    raise a `BackendException`."""

    backend = swift_backend()

    error = "Client Exception error."
    msg = f"Failed to write to object object.gz: {error}"

    def mock_get_container(*args, **kwargs):
        return (None, [])

    def mock_put_object(*args, **kwargs):
        return 1

    def mock_head_object(*args, **kwargs):
        raise ClientException(error)

    monkeypatch.setattr(backend.connection, "get_container", mock_get_container)
    monkeypatch.setattr(backend.connection, "put_object", mock_put_object)
    monkeypatch.setattr(backend.connection, "head_object", mock_head_object)

    with pytest.raises(BackendException, match=msg):
        backend.write(target="object.gz", data=[b"foo"])

    # When the `write` method fails, then no entry should be added to the history.
    assert not sorted(backend.history, key=itemgetter("id"))
    backend.close()


@pytest.mark.parametrize(
    "operation_type",
    [
        BaseOperationType.APPEND,
        BaseOperationType.DELETE,
        BaseOperationType.UPDATE,
    ],
)
def test_backends_data_swift_write_with_invalid_operation(
    operation_type,
    swift_backend,
    fs,
    settings_fs,
):
    """Test the `SwiftDataBackend.write` method, given an unsupported `operation_type`,
    should raise a `BackendParameterException`."""

    backend = swift_backend()

    msg = f"{operation_type.value.capitalize()} operation_type is not allowed"
    with pytest.raises(BackendParameterException, match=msg):
        backend.write(data=[b"foo"], operation_type=operation_type)

    # When the `write` method fails, then no entry should be added to the history.
    assert not sorted(backend.history, key=itemgetter("id"))
    backend.close()


def test_backends_data_swift_write_without_target(
    swift_backend, monkeypatch, fs, settings_fs
):
    """Test the `SwiftDataBackend.write` method, given no target, should write
    to the default container to a random object with the provided data.
    """

    # Freeze the ralph.utils.now() value.
    frozen_now = now()
    monkeypatch.setattr("ralph.backends.data.swift.now", lambda: frozen_now)

    # Freeze the uuid4() value.
    frozen_uuid4 = uuid4()
    monkeypatch.setattr("ralph.backends.data.swift.uuid4", lambda: frozen_uuid4)

    backend = swift_backend()

    # With empty data, `write` method is skipped
    count = backend.write(data=())

    assert backend.history == []
    assert count == 0

    listing = [{"name": "2020-04-29.gz"}, {"name": "object.gz"}]

    def mock_get_container(*args, **kwargs):
        return (None, [x["name"] for x in listing])

    def mock_put_object(container, obj, contents, chunk_size):
        list(contents)
        return 1

    def mock_head_object(*args, **kwargs):
        return {"content-length": 3}

    expected_filename = f"{frozen_now}-{frozen_uuid4}"
    monkeypatch.setattr(backend.connection, "get_container", mock_get_container)
    monkeypatch.setattr(backend.connection, "put_object", mock_put_object)
    monkeypatch.setattr(backend.connection, "head_object", mock_head_object)
    monkeypatch.setattr("ralph.backends.data.swift.now", lambda: frozen_now)

    count = backend.write(data=[{"foo": "bar"}, {"test": "toto"}])

    assert count == 2
    assert backend.history == [
        {
            "backend": "swift",
            "action": "write",
            "operation_type": BaseOperationType.CREATE.value,
            "id": f"container_name/{expected_filename}",
            "size": mock_head_object()["content-length"],
            "timestamp": frozen_now,
        }
    ]
    backend.close()


def test_backends_data_swift_close_with_failure(swift_backend, monkeypatch):
    """Test the `SwiftDataBackend.close` method."""

    backend = swift_backend()

    def mock_connection_error():
        """Swift backend connection close mock that raises a connection error."""
        raise ClientException({"Error": {}}, "error")

    monkeypatch.setattr(backend.connection, "close", mock_connection_error)

    with pytest.raises(BackendException, match="Failed to close Swift backend client"):
        backend.close()


def test_backends_data_swift_close(swift_backend, caplog):
    """Test the `SwiftDataBackend.close` method."""

    backend = swift_backend()

    # Not possible to connect to client after closing it
    backend.close()
    assert backend.status() == DataBackendStatus.ERROR

    # No client instantiated
    backend = swift_backend()
    backend._connection = None
    with caplog.at_level(logging.WARNING):
        backend.close()

    assert (
        "ralph.backends.data.swift",
        logging.WARNING,
        "No backend client to close.",
    ) in caplog.record_tuples
