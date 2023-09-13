"""Tests for Ralph S3 storage backend."""

import datetime
import json
import logging
import sys
from io import BytesIO

import boto3
import pytest
from moto import mock_s3

from ralph.conf import settings
from ralph.exceptions import BackendException, BackendParameterException


@mock_s3
def test_backends_storage_s3_storage_instantiation_should_raise_exception(
    s3, caplog
):  # pylint:disable=invalid-name
    """S3 backend instantiation test.

    Check that S3Storage raises BackendParameterException on failure.
    """
    # Regions outside us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create an invalid bucket in Moto's 'virtual' AWS account
    bucket_name = "my-test-bucket"
    s3_client.create_bucket(Bucket=bucket_name)

    error = "Not Found"
    caplog.set_level(logging.ERROR)

    with pytest.raises(BackendParameterException):
        s3()
    logger_name = "ralph.backends.storage.s3"
    msg = f"Unable to connect to the requested bucket: {error}"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]


@mock_s3
def test_backends_storage_s3_storage_instantiation_failure_should_not_raise_exception(
    s3,
):  # pylint:disable=invalid-name
    """S3 backend instantiation test.

    Check that S3Storage doesn't raise exceptions when the connection is
    successful.
    """
    # Regions outside us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    try:
        s3()
    except Exception:  # pylint:disable=broad-except
        pytest.fail("S3Storage should not raise exception on successful connection")


@mock_s3
def test_backends_storage_s3_list_should_yield_archive_names(
    moto_fs, s3, fs, settings_fs
):  # pylint:disable=unused-argument, invalid-name
    """S3 backend list test.

    Test that given S3Service.list method successfully connects to the S3
    storage, the S3Storage list method should yield the archives.
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

    history = [
        {"id": "2022-04-29.gz", "backend": "s3", "command": "read"},
        {"id": "2022-04-30.gz", "backend": "s3", "command": "read"},
    ]

    s3 = s3()
    try:
        response_list = s3.list()
        response_list_new = s3.list(new=True)
        response_list_details = s3.list(details=True)
    except Exception:  # pylint:disable=broad-except
        pytest.fail("S3Storage should not raise exception on successful list")

    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))

    assert list(response_list) == [x["name"] for x in listing]
    assert list(response_list_new) == ["2022-10-01.gz"]
    assert [x["Key"] for x in response_list_details] == [x["name"] for x in listing]


@mock_s3
def test_backends_storage_s3_list_on_empty_bucket_should_do_nothing(
    moto_fs, s3, fs
):  # pylint:disable=unused-argument, invalid-name
    """S3 backend list test.

    Test that given S3Service.list method successfully connects to the S3
    storage, the S3Storage list method on an empty bucket should do nothing.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    listing = []

    history = []

    s3 = s3()
    try:
        response_list = s3.list()
    except Exception:  # pylint:disable=broad-except
        pytest.fail("S3Storage should not raise exception on successful list")

    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))

    assert list(response_list) == [x["name"] for x in listing]


@mock_s3
def test_backends_storage_s3_list_with_failed_connection_should_log_the_error(
    moto_fs, s3, fs, caplog, settings_fs
):  # pylint:disable=unused-argument, invalid-name
    """S3 backend list test.

    Test that given S3Service.list method fails to retrieve the list of archives,
    the S3Storage list method should log the error and raise a BackendException.
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

    s3 = s3()
    s3.bucket_name = "wrong_name"

    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))
    caplog.set_level(logging.ERROR)
    error = "The specified bucket does not exist"
    msg = f"Failed to list the bucket wrong_name: {error}"

    with pytest.raises(BackendException, match=msg):
        next(s3.list())
    with pytest.raises(BackendException, match=msg):
        next(s3.list(new=True))
    with pytest.raises(BackendException, match=msg):
        next(s3.list(details=True))
    logger_name = "ralph.backends.storage.s3"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)] * 3


@mock_s3
def test_backends_storage_s3_read_with_valid_name_should_write_to_history(
    moto_fs, s3, monkeypatch, fs, settings_fs
):  # pylint:disable=unused-argument, invalid-name
    """S3 backend read test.

    Test that given S3Service.download method successfully retrieves from the
    S3 storage the object with the provided name (the object exists),
    the S3Storage read method should write the entry to the history.
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

    freezed_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    monkeypatch.setattr("ralph.backends.storage.s3.now", lambda: freezed_now)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))

    try:
        s3 = s3()
        list(s3.read("2022-09-29.gz"))
    except Exception:  # pylint:disable=broad-except
        pytest.fail("S3Storage should not raise exception on successful read")

    assert s3.history == [
        {
            "backend": "s3",
            "command": "read",
            "id": "2022-09-29.gz",
            "size": len(body),
            "fetched_at": freezed_now,
        }
    ]


@mock_s3
def test_backends_storage_s3_read_with_invalid_name_should_log_the_error(
    moto_fs, s3, fs, caplog, settings_fs
):  # pylint:disable=unused-argument, invalid-name
    """S3 backend read test.

    Test that given S3Service.download method fails to retrieve from the S3
    storage the object with the provided name (the object does not exists on S3),
    the S3Storage read method should log the error, not write to history and raise a
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

    fs.create_file(settings.HISTORY_FILE, contents=json.dumps([]))
    caplog.set_level(logging.ERROR)
    error = "The specified key does not exist."

    with pytest.raises(BackendException):
        s3 = s3()
        list(s3.read("invalid_name.gz"))
    logger_name = "ralph.backends.storage.s3"
    msg = f"Failed to download invalid_name.gz: {error}"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]
    assert s3.history == []


# pylint: disable=line-too-long
@pytest.mark.parametrize("overwrite", [False, True])
@pytest.mark.parametrize("new_archive", [False, True])
@mock_s3
def test_backends_storage_s3_write_should_write_to_history_new_or_overwritten_archives(  # noqa
    moto_fs, overwrite, new_archive, s3, monkeypatch, fs, caplog, settings_fs
):  # pylint:disable=unused-argument, invalid-name, too-many-arguments, too-many-locals
    """S3 backend write test.

    Test that given S3Service list/upload method successfully connects to the
    S3 storage, the S3Storage write method should update the history file when
    overwrite is True or when the name of the archive is not in the history.
    In case overwrite is False and the archive is in the history, the write method
    should raise a FileExistsError.
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

    history = [
        {"id": "2022-09-29.gz", "backend": "s3", "command": "read"},
        {"id": "2022-09-30.gz", "backend": "s3", "command": "read"},
    ]

    freezed_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    archive_name = "not_in_history.gz" if new_archive else "2022-09-29.gz"
    new_history_entry = [
        {
            "backend": "s3",
            "command": "write",
            "id": archive_name,
            "pushed_at": freezed_now,
        }
    ]

    stream_content = b"some contents in the stream file to upload"
    monkeypatch.setattr(sys, "stdin", BytesIO(stream_content))
    monkeypatch.setattr("ralph.backends.storage.s3.now", lambda: freezed_now)
    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))
    caplog.set_level(logging.ERROR)

    s3 = s3()
    if not overwrite and not new_archive:
        new_history_entry = []
        msg = f"{archive_name} already exists and overwrite is not allowed"
        with pytest.raises(FileExistsError, match=msg):
            s3.write(sys.stdin, archive_name, overwrite=overwrite)
        logger_name = "ralph.backends.storage.s3"
        assert caplog.record_tuples == [(logger_name, logging.ERROR, msg)]
    else:
        s3.write(sys.stdin, archive_name, overwrite=overwrite)
    assert s3.history == history + new_history_entry


@mock_s3
def test_backends_storage_s3_write_should_log_the_error(
    moto_fs, s3, monkeypatch, fs, caplog, settings_fs
):  # pylint:disable=unused-argument, invalid-name,too-many-arguments
    """S3 backend write test.

    Test that given S3Service.upload method fails to write the archive,
    the S3Storage write method should log the error, raise a BackendException
    and not write to history.
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

    history = [
        {"id": "2022-09-29.gz", "backend": "s3", "command": "read"},
        {"id": "2022-09-30.gz", "backend": "s3", "command": "read"},
    ]

    fs.create_file(settings.HISTORY_FILE, contents=json.dumps(history))
    caplog.set_level(logging.ERROR)

    s3 = s3()

    error = "Failed to upload"

    stream_content = b"some contents in the stream file to upload"
    monkeypatch.setattr(sys, "stdin", BytesIO(stream_content))

    with pytest.raises(BackendException):
        s3.write(sys.stdin, "", overwrite=True)
    logger_name = "ralph.backends.storage.s3"
    assert caplog.record_tuples == [(logger_name, logging.ERROR, error)]
    assert s3.history == history


@mock_s3
def test_backends_storage_url_should_concatenate_the_storage_url_and_name(
    s3,
):  # pylint:disable=invalid-name
    """S3 backend url test.

    Check the url method returns `bucket_name.s3.default_region
    .amazonaws.com/name`.
    """
    # Regions outside of us-east-1 require the appropriate LocationConstraint
    s3_client = boto3.client("s3", region_name="us-east-1")
    # Create a valid bucket in Moto's 'virtual' AWS account
    bucket_name = "bucket_name"
    s3_client.create_bucket(Bucket=bucket_name)

    assert s3().url("name") == "bucket_name.s3.default-region.amazonaws.com/name"
