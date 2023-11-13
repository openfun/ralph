"""Tests for Ralph S3 data backend."""

import datetime
import json
import logging
import re
from collections import namedtuple

import boto3
import pytest
from botocore.exceptions import ClientError, ResponseStreamingError
from moto import mock_s3

from ralph.backends.data.base import BaseOperationType, DataBackendStatus
from ralph.backends.data.s3 import S3DataBackend, S3DataBackendSettings, S3Query
from ralph.exceptions import BackendException, BackendParameterException


def test_backends_data_s3_default_instantiation(monkeypatch, fs):
    """Test the `S3DataBackend` default instantiation."""
    fs.create_file(".env")
    backend_settings_names = [
        "ACCESS_KEY_ID",
        "SECRET_ACCESS_KEY",
        "SESSION_TOKEN",
        "ENDPOINT_URL",
        "DEFAULT_REGION",
        "DEFAULT_BUCKET_NAME",
        "DEFAULT_CHUNK_SIZE",
        "LOCALE_ENCODING",
    ]
    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__S3__{name}", raising=False)

    assert S3DataBackend.name == "s3"
    assert S3DataBackend.query_class == S3Query
    assert S3DataBackend.default_operation_type == BaseOperationType.CREATE
    assert S3DataBackend.settings_class == S3DataBackendSettings
    backend = S3DataBackend()
    assert backend.default_bucket_name is None
    assert backend.default_chunk_size == 4096
    assert backend.locale_encoding == "utf8"

    # Test overriding default values with environment variables.
    monkeypatch.setenv("RALPH_BACKENDS__DATA__S3__DEFAULT_CHUNK_SIZE", 1)
    backend = S3DataBackend()
    assert backend.default_chunk_size == 1


def test_backends_data_s3_instantiation_with_settings():
    """Test the `S3DataBackend` instantiation with settings."""
    settings_ = S3DataBackend.settings_class(
        ACCESS_KEY_ID="access_key",
        SECRET_ACCESS_KEY="secret",
        SESSION_TOKEN="session_token",
        ENDPOINT_URL="http://endpoint/url",
        DEFAULT_REGION="us-west-2",
        DEFAULT_BUCKET_NAME="bucket",
        DEFAULT_CHUNK_SIZE=1000,
        LOCALE_ENCODING="utf-16",
    )
    backend = S3DataBackend(settings_)
    assert backend.default_bucket_name == "bucket"
    assert backend.default_chunk_size == 1000
    assert backend.locale_encoding == "utf-16"

    try:
        S3DataBackend(settings_)
    except Exception as err:  # noqa: BLE001
        pytest.fail(f"S3DataBackend should not raise exceptions: {err}")


@mock_s3
def test_backends_data_s3_status(s3_backend):
    """Test the `S3DataBackend.status` method."""

    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")

    backend = s3_backend()
    assert backend.status() == DataBackendStatus.ERROR
    backend.close()

    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    backend = s3_backend()
    assert backend.status() == DataBackendStatus.OK
    backend.close()


@mock_s3
def test_backends_data_s3_list_should_yield_archive_names(
    s3_backend,
):
    """Test that given `S3DataBackend.list` method successfully connects to the S3
    data, the S3 backend list method should yield the archives.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-04-29.gz",
        Body=json.dumps({"id": "1", "foo": "bar"}),
    )

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-04-30.gz",
        Body=json.dumps({"id": "2", "some": "data"}),
    )

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-10-01.gz",
        Body=json.dumps({"id": "3", "other": "info"}),
    )

    listing = [
        {"name": "2022-04-29.gz"},
        {"name": "2022-04-30.gz"},
        {"name": "2022-10-01.gz"},
    ]

    backend = s3_backend()

    backend.history.extend(
        [
            {"id": "bucket_name/2022-04-29.gz", "backend": "s3", "command": "read"},
            {"id": "bucket_name/2022-04-30.gz", "backend": "s3", "command": "read"},
        ]
    )

    try:
        response_list = backend.list()
        response_list_new = backend.list(new=True)
        response_list_details = backend.list(details=True)
    except Exception:  # noqa: BLE001
        pytest.fail("S3 backend should not raise exception on successful list")

    assert list(response_list) == [x["name"] for x in listing]
    assert list(response_list_new) == ["2022-10-01.gz"]
    assert [x["Key"] for x in response_list_details] == [x["name"] for x in listing]
    backend.close()


@mock_s3
def test_backends_data_s3_list_on_empty_bucket_should_do_nothing(
    s3_backend,
):
    """Test that given `S3DataBackend.list` method successfully connects to the S3
    data, the S3 backend list method on an empty bucket should do nothing.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    listing = []

    backend = s3_backend()

    backend.clean_history(lambda *_: True)
    try:
        response_list = backend.list()
    except Exception:  # noqa: BLE001
        pytest.fail("S3 backend should not raise exception on successful list")

    assert list(response_list) == [x["name"] for x in listing]
    backend.close()


@mock_s3
def test_backends_data_s3_list_with_failed_connection_should_log_the_error(
    s3_backend, caplog
):
    """Test that given `S3DataBackend.list` method fails to retrieve the list of
    archives, the S3 backend list method should log the error and raise a
    BackendException.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-04-29.gz",
        Body=json.dumps({"id": "1", "foo": "bar"}),
    )

    backend = s3_backend()

    backend.clean_history(lambda *_: True)

    msg = "Failed to list the bucket wrong_name: The specified bucket does not exist"

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            next(backend.list(target="wrong_name"))
        with pytest.raises(BackendException, match=msg):
            next(backend.list(target="wrong_name", new=True))
        with pytest.raises(BackendException, match=msg):
            next(backend.list(target="wrong_name", details=True))

    assert (
        list(
            filter(
                lambda record: record[1] == logging.ERROR,
                caplog.record_tuples,
            )
        )
        == [("ralph.backends.data.s3", logging.ERROR, msg)] * 3
    )
    backend.close()


@mock_s3
def test_backends_data_s3_read_with_valid_name_should_write_to_history(
    s3_backend,
    monkeypatch,
):
    """Test that given `S3DataBackend.list` method successfully retrieves from the
    S3 data the object with the provided name (the object exists),
    the S3 backend read method should write the entry to the history.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    raw_body = b"some contents in the body"
    json_body = '{"id":"foo"}'

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-09-29.gz",
        Body=raw_body,
    )

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-09-30.gz",
        Body=json_body,
    )

    freezed_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    monkeypatch.setattr("ralph.backends.data.s3.now", lambda: freezed_now)

    backend = s3_backend()
    backend.clean_history(lambda *_: True)

    list(
        backend.read(
            query="2022-09-29.gz",
            target=bucket_name,
            chunk_size=1000,
            raw_output=True,
        )
    )

    assert {
        "backend": "s3",
        "action": "read",
        "id": f"{bucket_name}/2022-09-29.gz",
        "size": len(raw_body),
        "timestamp": freezed_now,
    } in backend.history

    list(
        backend.read(
            query="2022-09-30.gz",
            raw_output=False,
        )
    )

    assert {
        "backend": "s3",
        "action": "read",
        "id": f"{bucket_name}/2022-09-30.gz",
        "size": len(json_body),
        "timestamp": freezed_now,
    } in backend.history
    backend.close()


@mock_s3
def test_backends_data_s3_read_with_invalid_output_should_log_the_error(
    s3_backend, caplog
):
    """Test that given `S3DataBackend.read` method fails to serialize the object, the
    S3 backend read method should log the error, not write to history and raise a
    BackendException.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    body = b"some contents in the body"

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-09-29.gz",
        Body=body,
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            backend = s3_backend()
            list(backend.read(query="2022-09-29.gz", raw_output=False))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        "Failed to decode JSON: Expecting value: line 1 column 1 (char 0),"
        " for document: b'some contents in the body', at line 0",
    ) in caplog.record_tuples

    backend.clean_history(lambda *_: True)
    backend.close()


@mock_s3
def test_backends_data_s3_read_with_invalid_name_should_log_the_error(
    s3_backend, caplog
):
    """Test that given `S3DataBackend.read` method fails to retrieve from the S3
    data the object with the provided name (the object does not exists on S3),
    the S3 backend read method should log the error, not write to history and raise a
    BackendException.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    body = b"some contents in the body"

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-09-29.gz",
        Body=body,
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendParameterException):
            backend = s3_backend()
            list(backend.read(query=None, target=bucket_name))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        "Invalid S3Query default query: [{'loc': ('query_string',), 'msg': "
        "'field required', 'type': 'value_error.missing'}]",
    ) in caplog.record_tuples

    backend.clean_history(lambda *_: True)
    backend.close()


@mock_s3
def test_backends_data_s3_read_with_wrong_name_should_log_the_error(s3_backend, caplog):
    """Test that given `S3DataBackend.read` method fails to retrieve from the S3
    data the object with the provided name (the object does not exists on S3),
    the S3 backend read method should log the error, not write to history and raise a
    BackendException.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    body = b"some contents in the body"

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-09-29.gz",
        Body=body,
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            backend = s3_backend()
            backend.clean_history(lambda *_: True)
            list(backend.read(query="invalid_name.gz", target=bucket_name))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        "Failed to download invalid_name.gz: The specified key does not exist.",
    ) in caplog.record_tuples

    assert backend.history == []
    backend.close()


@mock_s3
def test_backends_data_s3_read_with_iter_error_should_log_the_error(
    s3_backend, caplog, monkeypatch
):
    """Test that given `S3DataBackend.read` method fails to iterate through the result
    from the S3 data the object, the S3 backend read method should log the error,
    not write to history and raise a BackendException.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    body = b"some contents in the body"

    object_name = "2022-09-29.gz"

    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_name,
        Body=body,
    )

    def mock_get_object(*args, **kwargs):  # pylint: disable=unused-argument
        """Mock the boto3 client.get_object method raising an exception on iteration."""

        def raising_iter_chunks(*_, **__):  # pylint: disable=unused-argument
            raise ResponseStreamingError(error="error")

        return {"Body": namedtuple("_", "iter_chunks")(raising_iter_chunks)}

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            backend = s3_backend()
            monkeypatch.setattr(backend.client, "get_object", mock_get_object)
            backend.clean_history(lambda *_: True)
            list(backend.read(query=object_name, target=bucket_name, raw_output=True))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        f"Failed to read chunk from object {object_name}",
    ) in caplog.record_tuples
    assert backend.history == []
    backend.close()


@pytest.mark.parametrize(
    "operation_type",
    [None, BaseOperationType.CREATE, BaseOperationType.INDEX],
)
@mock_s3
def test_backends_data_s3_write_with_parameter_error(
    operation_type, s3_backend, caplog
):
    """Test the `S3DataBackend.write` method, given a target matching an
    existing object and a `CREATE` or `INDEX` `operation_type`, should raise a
    `FileExistsError`.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    body = b"some contents in the body"

    s3_client.put_object(
        Bucket=bucket_name,
        Key="2022-09-29.gz",
        Body=body,
    )

    object_name = "2022-09-29.gz"
    some_content = b"some contents in the stream file to upload"

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            backend = s3_backend()
            backend.clean_history(lambda *_: True)
            backend.write(
                data=some_content, target=object_name, operation_type=operation_type
            )

    msg = (
        f"{object_name} already exists and overwrite is not allowed for operation"
        f" {operation_type if operation_type is not None else BaseOperationType.CREATE}"
    )

    assert ("ralph.backends.data.s3", logging.ERROR, msg) in caplog.record_tuples
    assert backend.history == []
    backend.close()


@pytest.mark.parametrize(
    "operation_type",
    [BaseOperationType.APPEND, BaseOperationType.DELETE],
)
def test_backends_data_s3_write_with_append_or_delete_operation(
    s3_backend, operation_type
):
    """Test the `S3DataBackend.write` method, given an `APPEND`
    `operation_type`, should raise a `BackendParameterException`.
    """

    backend = s3_backend()
    with pytest.raises(
        BackendParameterException,
        match=f"{operation_type.name} operation_type is not allowed.",
    ):
        backend.write(data=[b"foo"], operation_type=operation_type)
    backend.close()


@pytest.mark.parametrize(
    "operation_type",
    [BaseOperationType.CREATE, BaseOperationType.INDEX],
)
@mock_s3
def test_backends_data_s3_write_with_create_index_operation(
    operation_type, s3_backend, monkeypatch, caplog
):
    """Test the `S3DataBackend.write` method, given a target matching an
    existing object and a `CREATE` or `INDEX` `operation_type`, should add
    an entry to the History.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    freezed_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    monkeypatch.setattr("ralph.backends.data.s3.now", lambda: freezed_now)

    object_name = "new-archive.gz"
    some_content = b"some contents in the stream file to upload"
    data = [some_content, some_content, some_content]
    backend = s3_backend()
    backend.clean_history(lambda *_: True)

    response = backend.write(
        data=data,
        target=object_name,
        operation_type=operation_type,
    )

    assert response == 3
    assert {
        "backend": "s3",
        "action": "write",
        "operation_type": operation_type.value,
        "id": f"{bucket_name}/{object_name}",
        "size": len(some_content) * 3,
        "timestamp": freezed_now,
    } in backend.history

    object_name = "new-archive2.gz"
    other_content = {"some": "content"}

    data = [other_content, other_content]
    response = backend.write(
        data=data,
        target=object_name,
        operation_type=operation_type,
    )

    assert response == 2
    assert {
        "backend": "s3",
        "action": "write",
        "operation_type": operation_type.value,
        "id": f"{bucket_name}/{object_name}",
        "size": len(bytes(f"{json.dumps(other_content)}\n", encoding="utf8")) * 2,
        "timestamp": freezed_now,
    } in backend.history

    assert list(backend.read(query=object_name, raw_output=False)) == data

    object_name = "new-archive3.gz"
    date = datetime.datetime(2023, 6, 30, 8, 42, 15, 554892)

    data = [{"some": "content", "datetime": date}]

    msg = (
        "Failed to encode JSON: Object of type datetime is not JSON serializable, "
        f"for document: {data[0]}, at line 0"
    )
    with caplog.at_level(logging.WARNING):
        # Without ignoring error
        with pytest.raises(BackendException, match=re.escape(msg)):
            response = backend.write(
                data=data,
                target=object_name,
                operation_type=operation_type,
                ignore_errors=False,
            )

        # Ignoring error
        response = backend.write(
            data=data,
            target=object_name,
            operation_type=operation_type,
            ignore_errors=True,
        )

    assert list(
        filter(
            lambda record: record[1] in [logging.ERROR, logging.WARNING],
            caplog.record_tuples,
        )
    ) == (
        [
            ("ralph.backends.data.s3", logging.ERROR, msg),
            ("ralph.backends.data.s3", logging.WARNING, msg),
        ]
    )
    backend.close()


@mock_s3
def test_backends_data_s3_write_with_no_data_should_skip(
    s3_backend,
):
    """Test the `S3DataBackend.write` method, given no data to write,
    should skip and return 0.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    object_name = "new-archive.gz"

    backend = s3_backend()
    response = backend.write(
        data=[],
        target=object_name,
        operation_type=BaseOperationType.CREATE,
    )
    assert response == 0
    backend.close()


@mock_s3
def test_backends_data_s3_write_with_failure_should_log_the_error(
    s3_backend,
):
    """Test the `S3DataBackend.write` method, given a connection failure,
    should raise a `BackendException`.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    object_name = "new-archive.gz"
    body = b"some contents in the body"
    error = "Failed to upload"

    def raise_client_error(*args, **kwargs):
        raise ClientError({"Error": {}}, "error")

    backend = s3_backend()
    backend.client.put_object = raise_client_error

    with pytest.raises(BackendException, match=error):
        backend.write(
            data=[body],
            target=object_name,
            operation_type=BaseOperationType.CREATE,
        )
    backend.close()


def test_backends_data_s3_close_with_failure(s3_backend, monkeypatch):
    """Test the `S3DataBackend.close` method."""

    backend = s3_backend()

    def mock_connection_error():
        """S3 backend client close mock that raises a connection error."""
        raise ClientError({"Error": {}}, "error")

    monkeypatch.setattr(backend.client, "close", mock_connection_error)

    with pytest.raises(BackendException, match="Failed to close S3 backend client"):
        backend.close()


@mock_s3
def test_backends_data_s3_close(s3_backend, caplog):
    """Test the `S3DataBackend.close` method."""

    # No client instantiated
    backend = s3_backend()
    backend._client = None
    with caplog.at_level(logging.WARNING):
        backend.close()

    assert (
        "ralph.backends.data.s3",
        logging.WARNING,
        "No backend client to close.",
    ) in caplog.record_tuples
