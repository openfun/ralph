"""Tests for Ralph S3 data backend."""

import datetime
import json
import logging

import boto3
import pytest
from botocore.exceptions import ClientError, ResponseStreamingError
from moto import mock_s3

from ralph.backends.data.base import BaseOperationType, BaseQuery, DataBackendStatus
from ralph.backends.data.s3 import S3DataBackend, S3DataBackendSettings
from ralph.exceptions import BackendException, BackendParameterException


def test_backends_data_s3_backend_default_instantiation(
    monkeypatch, fs
):  # pylint: disable=invalid-name
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
    assert S3DataBackend.query_model == BaseQuery
    assert S3DataBackend.default_operation_type == BaseOperationType.CREATE
    assert S3DataBackend.settings_class == S3DataBackendSettings
    backend = S3DataBackend()
    assert backend.default_bucket_name is None
    assert backend.default_chunk_size == 4096
    assert backend.locale_encoding == "utf8"


def test_backends_data_s3_data_backend_instantiation_with_settings():
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
    except Exception as err:  # pylint:disable=broad-except
        pytest.fail(f"S3DataBackend should not raise exceptions: {err}")


@mock_s3
def test_backends_data_s3_data_backend_status_method(s3_backend):
    """Test the `S3DataBackend.status` method."""

    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")

    assert s3_backend().status() == DataBackendStatus.ERROR

    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    assert s3_backend().status() == DataBackendStatus.OK


@mock_s3
def test_backends_data_s3_data_backend_list_should_yield_archive_names(
    s3_backend,
):  # pylint: disable=invalid-name
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

    s3 = s3_backend()

    s3.history.extend(
        [
            {"id": "bucket_name/2022-04-29.gz", "backend": "s3", "command": "read"},
            {"id": "bucket_name/2022-04-30.gz", "backend": "s3", "command": "read"},
        ]
    )

    try:
        response_list = s3.list()
        response_list_new = s3.list(new=True)
        response_list_details = s3.list(details=True)
    except Exception:  # pylint:disable=broad-except
        pytest.fail("S3 backend should not raise exception on successful list")

    assert list(response_list) == [x["name"] for x in listing]
    assert list(response_list_new) == ["2022-10-01.gz"]
    assert [x["Key"] for x in response_list_details] == [x["name"] for x in listing]


@mock_s3
def test_backends_data_s3_list_on_empty_bucket_should_do_nothing(
    s3_backend,
):  # pylint: disable=invalid-name
    """Test that given `S3DataBackend.list` method successfully connects to the S3
    data, the S3 backend list method on an empty bucket should do nothing.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    listing = []

    s3 = s3_backend()

    s3.clean_history(lambda *_: True)
    try:
        response_list = s3.list()
    except Exception:  # pylint:disable=broad-except
        pytest.fail("S3 backend should not raise exception on successful list")

    assert list(response_list) == [x["name"] for x in listing]


@mock_s3
def test_backends_data_s3_list_with_failed_connection_should_log_the_error(
    s3_backend, caplog
):  # pylint: disable=invalid-name
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

    s3 = s3_backend()

    s3.clean_history(lambda *_: True)

    msg = "Failed to list the bucket wrong_name: The specified bucket does not exist"

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            next(s3.list(target="wrong_name"))
        with pytest.raises(BackendException, match=msg):
            next(s3.list(target="wrong_name", new=True))
        with pytest.raises(BackendException, match=msg):
            next(s3.list(target="wrong_name", details=True))

    assert (
        list(
            filter(
                lambda record: record[1] == logging.ERROR,
                caplog.record_tuples,
            )
        )
        == [("ralph.backends.data.s3", logging.ERROR, msg)] * 3
    )


@mock_s3
def test_backends_data_s3_read_with_valid_name_should_write_to_history(
    s3_backend,
    monkeypatch,
):  # pylint: disable=invalid-name
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

    s3 = s3_backend()
    s3.clean_history(lambda *_: True)

    list(
        s3.read(
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
    } in s3.history

    list(
        s3.read(
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
    } in s3.history


@mock_s3
def test_backends_data_s3_read_with_invalid_output_should_log_the_error(
    s3_backend, caplog
):  # pylint: disable=invalid-name
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
            s3 = s3_backend()
            list(s3.read(query="2022-09-29.gz", raw_output=False))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        "Raised error: Expecting value: line 1 column 1 (char 0)",
    ) in caplog.record_tuples

    s3.clean_history(lambda *_: True)


@mock_s3
def test_backends_data_s3_read_with_invalid_name_should_log_the_error(
    s3_backend, caplog
):  # pylint: disable=invalid-name
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
            s3 = s3_backend()
            list(s3.read(query=None, target=bucket_name))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        "Invalid query. The query should be a valid object name.",
    ) in caplog.record_tuples

    s3.clean_history(lambda *_: True)


@mock_s3
def test_backends_data_s3_read_with_wrong_name_should_log_the_error(
    s3_backend, caplog
):  # pylint: disable=invalid-name
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
            s3 = s3_backend()
            s3.clean_history(lambda *_: True)
            list(s3.read(query="invalid_name.gz", target=bucket_name))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        "Failed to download invalid_name.gz: The specified key does not exist.",
    ) in caplog.record_tuples

    assert s3.history == []


@mock_s3
def test_backends_data_s3_read_with_iter_error_should_log_the_error(
    s3_backend, caplog, monkeypatch
):  # pylint: disable=invalid-name
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

    def mock_read_raw(*args, **kwargs):
        raise ResponseStreamingError(error="error")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            s3 = s3_backend()
            monkeypatch.setattr(s3, "_read_raw", mock_read_raw)
            s3.clean_history(lambda *_: True)
            list(s3.read(query=object_name, target=bucket_name, raw_output=True))

    assert (
        "ralph.backends.data.s3",
        logging.ERROR,
        f"Failed to read chunk from object {object_name}",
    ) in caplog.record_tuples
    assert s3.history == []


@pytest.mark.parametrize(
    "operation_type",
    [None, BaseOperationType.CREATE, BaseOperationType.INDEX],
)
@mock_s3
def test_backends_data_s3_write_method_with_parameter_error(
    operation_type, s3_backend, caplog
):  # pylint: disable=invalid-name
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
            s3 = s3_backend()
            s3.clean_history(lambda *_: True)
            s3.write(
                data=some_content, target=object_name, operation_type=operation_type
            )

    msg = (
        f"{object_name} already exists and overwrite is not allowed for operation"
        f" {operation_type if operation_type is not None else BaseOperationType.CREATE}"
    )

    assert ("ralph.backends.data.s3", logging.ERROR, msg) in caplog.record_tuples
    assert s3.history == []


@pytest.mark.parametrize(
    "operation_type",
    [BaseOperationType.APPEND, BaseOperationType.DELETE],
)
def test_backends_data_s3_data_backend_write_method_with_append_or_delete_operation(
    s3_backend, operation_type
):
    """Test the `S3DataBackend.write` method, given an `APPEND`
    `operation_type`, should raise a `BackendParameterException`.
    """
    # pylint: disable=invalid-name
    backend = s3_backend()
    with pytest.raises(
        BackendParameterException,
        match=f"{operation_type.name} operation_type is not allowed.",
    ):
        backend.write(data=[b"foo"], operation_type=operation_type)


@pytest.mark.parametrize(
    "operation_type",
    [BaseOperationType.CREATE, BaseOperationType.INDEX],
)
@mock_s3
def test_backends_data_s3_write_method_with_create_index_operation(
    operation_type, s3_backend, monkeypatch, caplog
):  # pylint: disable=invalid-name
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
    s3 = s3_backend()
    s3.clean_history(lambda *_: True)

    response = s3.write(
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
    } in s3.history

    object_name = "new-archive2.gz"
    other_content = {"some": "content"}

    data = [other_content, other_content]
    response = s3.write(
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
    } in s3.history

    assert list(s3.read(query=object_name, raw_output=False)) == data

    object_name = "new-archive3.gz"
    date = datetime.datetime(2023, 6, 30, 8, 42, 15, 554892)

    data = [{"some": "content", "datetime": date}]

    error = "Object of type datetime is not JSON serializable"

    with caplog.at_level(logging.ERROR):
        # Without ignoring error
        with pytest.raises(BackendException, match=error):
            response = s3.write(
                data=data,
                target=object_name,
                operation_type=operation_type,
                ignore_errors=False,
            )

        # Ignoring error
        response = s3.write(
            data=data,
            target=object_name,
            operation_type=operation_type,
            ignore_errors=True,
        )

    assert list(
        filter(
            lambda record: record[1] == logging.ERROR,
            caplog.record_tuples,
        )
    ) == (
        [
            (
                "ralph.backends.data.s3",
                logging.ERROR,
                f"Failed to encode JSON: {error}, for document {data[0]}",
            )
        ]
        * 2
    )


@mock_s3
def test_backends_data_s3_write_method_with_no_data_should_skip(
    s3_backend,
):  # pylint: disable=invalid-name
    """Test the `S3DataBackend.write` method, given no data to write,
    should skip and return 0.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    object_name = "new-archive.gz"

    s3 = s3_backend()
    response = s3.write(
        data=[],
        target=object_name,
        operation_type=BaseOperationType.CREATE,
    )
    assert response == 0


@mock_s3
def test_backends_data_s3_write_method_with_failure_should_log_the_error(
    s3_backend,
):  # pylint: disable=invalid-name
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

    s3 = s3_backend()
    s3.client.put_object = raise_client_error

    with pytest.raises(BackendException, match=error):
        s3.write(
            data=[body],
            target=object_name,
            operation_type=BaseOperationType.CREATE,
        )
