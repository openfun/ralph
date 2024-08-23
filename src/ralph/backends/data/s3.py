"""S3 data backend for Ralph."""

import logging
from io import IOBase
from typing import Iterable, Iterator, Optional, Union
from uuid import uuid4

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.client import BaseClient
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    ParamValidationError,
    ReadTimeoutError,
    ResponseStreamingError,
)
from pydantic import PositiveInt
from pydantic_settings import SettingsConfigDict
from requests_toolbelt import StreamingIterator

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    DataBackendStatus,
    Listable,
    Writable,
)
from ralph.backends.data.mixins import HistoryMixin
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now, parse_iterable_to_dict

logger = logging.getLogger(__name__)


class S3DataBackendSettings(BaseDataBackendSettings):
    """S3 data backend default configuration.

    Attributes:
        ACCESS_KEY_ID (str): The access key id for the S3 account.
        SECRET_ACCESS_KEY (str): The secret key for the S3 account.
        SESSION_TOKEN (str): The session token for the S3 account.
        ENDPOINT_URL (str): The endpoint URL of the S3.
        DEFAULT_REGION (str): The default region used in instantiating the client.
        DEFAULT_BUCKET_NAME (str): The default bucket name targeted.
        LOCALE_ENCODING (str): The encoding used for writing dictionaries to objects.
        READ_CHUNK_SIZE (str): The default chunk size for reading objects.
        WRITE_CHUNK_SIZE (str): The default chunk size for writing objects.
    """

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__DATA__S3__"),
    }

    ACCESS_KEY_ID: Optional[str] = None
    SECRET_ACCESS_KEY: Optional[str] = None
    SESSION_TOKEN: Optional[str] = None
    ENDPOINT_URL: Optional[str] = None
    DEFAULT_REGION: Optional[str] = None
    DEFAULT_BUCKET_NAME: Optional[str] = None
    READ_CHUNK_SIZE: int = 4096
    WRITE_CHUNK_SIZE: int = 4096


class S3DataBackend(
    BaseDataBackend[S3DataBackendSettings, str], Writable, Listable, HistoryMixin
):
    """S3 data backend."""

    name = "s3"
    default_operation_type = BaseOperationType.CREATE
    unsupported_operation_types = {
        BaseOperationType.APPEND,
        BaseOperationType.DELETE,
        BaseOperationType.UPDATE,
    }

    def __init__(self, settings: Optional[S3DataBackendSettings] = None):
        """Instantiate the AWS S3 client."""
        super().__init__(settings)
        self.default_bucket_name = self.settings.DEFAULT_BUCKET_NAME
        self._client = None

    @property
    def client(self) -> BaseClient:
        """Create a boto3 client if it doesn't exist."""
        if not self._client:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=self.settings.ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.SECRET_ACCESS_KEY,
                aws_session_token=self.settings.SESSION_TOKEN,
                region_name=self.settings.DEFAULT_REGION,
                endpoint_url=self.settings.ENDPOINT_URL,
            )
        return self._client

    def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """
        try:
            self.client.head_bucket(Bucket=self.default_bucket_name)
        except (ClientError, EndpointConnectionError):
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
        """List objects for the target bucket.

        Args:
            target (str or None): The target bucket to list from.
                If target is `None`, the `default_bucket_name` is used instead.
            details (bool): Get detailed object information instead of just object name.
            new (bool): Given the history, list only unread files.

        Yield:
            str: The next object name. (If details is False).
            dict: The next object details. (If details is True).

        Raise:
            BackendException: If a failure occurs.
        """
        if target is None:
            target = self.default_bucket_name

        objects_to_skip = set()
        if new:
            objects_to_skip = set(self.get_command_history(self.name, "read"))

        try:
            paginator = self.client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=target)
            for objects in page_iterator:
                if "Contents" not in objects:
                    continue
                for obj in objects["Contents"]:
                    if new and f"{target}/{obj['Key']}" in objects_to_skip:
                        continue
                    if details:
                        obj["LastModified"] = obj["LastModified"].isoformat()
                        yield obj
                    else:
                        yield obj["Key"]
        except ClientError as err:
            error_msg = err.response["Error"]["Message"]
            msg = "Failed to list the bucket %s: %s"
            logger.error(msg, target, error_msg)
            raise BackendException(msg % (target, error_msg)) from err

    def read(  # noqa: PLR0913
        self,
        query: Optional[str] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
        """Read an object matching the `query` in the `target` bucket and yield it.

        Args:
            query (str): The ID of the object to read.
            target (str or None): The target bucket containing the object.
                If target is `None`, the `default_bucket` is used instead.
            chunk_size (int or None): The number of records or bytes to read in one
                batch, depending on whether the records are dictionaries or bytes.
                If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default) or `0`, there is no maximum.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a connection failure occurs while reading from S3 or
                during object encoding and `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )

    def _read_bytes(
        self,
        query: str,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        target = self.default_bucket_name if target is None else target
        response = self._get_object(target, query)
        try:
            yield from response["Body"].iter_chunks(chunk_size)
        except (ReadTimeoutError, ResponseStreamingError) as err:
            msg = "Failed to read chunk from object %s"
            logger.error(msg, query)
            raise BackendException(msg % (query)) from err

        # Archive fetched, add a new entry to the history.
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": target.rstrip("/") + "/" + query,
                "size": response["ContentLength"],
                "timestamp": now(),
            }
        )

    def _read_dicts(
        self,
        query: str,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        target = self.default_bucket_name if target is None else target
        response = self._get_object(target, query)
        try:
            lines = response["Body"].iter_lines(chunk_size)
            yield from parse_iterable_to_dict(lines, ignore_errors)
        except (ReadTimeoutError, ResponseStreamingError) as err:
            msg = "Failed to read chunk from object %s"
            logger.error(msg, query)
            raise BackendException(msg % query) from err

        # Archive fetched, add a new entry to the history.
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": target.rstrip("/") + "/" + query,
                "size": response["ContentLength"],
                "timestamp": now(),
            }
        )

    def _get_object(self, bucket: Optional[str], key: str) -> dict:
        """Validate bucket (target) and key (query) and return the S3 object."""
        if not bucket:
            msg = "The target bucket is not set"
            logger.error(msg)
            raise BackendParameterException(msg)

        if not key:
            msg = "The object ID query is not set"
            logger.error(msg)
            raise BackendParameterException(msg)

        try:
            return self.client.get_object(Bucket=bucket, Key=key)
        except (ClientError, EndpointConnectionError) as error:
            error_msg = error
            if isinstance(error, ClientError):
                error_msg = error.response["Error"]["Message"]

            msg = "Failed to download %s: %s"
            logger.error(msg, key, error_msg)
            raise BackendException(msg % (key, error_msg)) from error

    def write(
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` records to the `target` bucket and return their count.

        Args:
            data (Iterable or IOBase): The data to write.
            target (str or None): The target bucket and the target object
                separated by a `/`.
                If target is `None`, the default bucket is used and a random
                (uuid4) object is created.
                If target does not contain a `/`, it is assumed to be the
                target object and the default bucket is used.
            chunk_size (int or None): The chunk size when writing objects by batch.
                If `chunk_size` is `None` it defaults to `WRITE_CHUNK_SIZE`.
            ignore_errors (bool): If `True`, errors during decoding and encoding of
                records are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write
                operation.
                If operation_type is `CREATE` or `INDEX`, the target object is
                expected to be absent. If the target object exists a
                `BackendException` is raised.

        Return:
            int: The number of written objects.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_dicts(
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        return super()._write_dicts(
            data, target, chunk_size, ignore_errors, operation_type
        )

    def _write_bytes(
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        if not target:
            target = f"{self.default_bucket_name}/{now()}-{uuid4()}"
            logger.info(
                "Target not specified; using default bucket with random file name: %s",
                target,
            )
        elif "/" not in target:
            target = f"{self.default_bucket_name}/{target}"
            logger.info(
                "Target not specified; using default bucket: %s",
                target,
            )

        target_bucket, target_object = target.split("/", 1)
        if target_object in list(self.list(target=target_bucket)):
            msg = "%s already exists and overwrite is not allowed for operation %s"
            logger.error(msg, target_object, operation_type)
            raise BackendException(msg % (target_object, operation_type))

        logger.info("Creating archive: %s", target_object)
        counter = {"count": 0}
        data = self._count(data, counter)

        # Using StreamingIterator from requests-toolbelt but without specifying a size
        # as we will not use it. It implements the `read` method for iterators.
        file_object = StreamingIterator(0, data)

        try:
            self.client.upload_fileobj(
                Bucket=target_bucket,
                Key=target_object,
                Fileobj=file_object,
                Config=TransferConfig(multipart_chunksize=chunk_size),
            )
            response = self.client.head_object(Bucket=target_bucket, Key=target_object)
        except (ClientError, ParamValidationError, EndpointConnectionError) as error:
            msg = "Failed to upload %s"
            logger.error(msg, target)
            raise BackendException(msg % target) from error

        # Archive written, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "action": "write",
                "operation_type": operation_type.value,
                "id": target,
                "size": response["ContentLength"],
                "timestamp": now(),
            }
        )

        return counter["count"]

    def close(self) -> None:
        """Close the S3 backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            logger.warning("No backend client to close.")
            return

        try:
            self.client.close()
        except ClientError as error:
            msg = "Failed to close S3 backend client: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    @staticmethod
    def _count(statements: Iterable, counter: dict) -> Iterator:
        """Count the elements in the `statements` Iterable and yield element."""
        for statement in statements:
            yield statement
            counter["count"] += 1
