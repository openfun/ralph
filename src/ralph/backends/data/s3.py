"""S3 data backend for Ralph."""

import logging
from io import IOBase
from typing import Iterable, Iterator, Tuple, Union
from uuid import uuid4

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    ParamValidationError,
    ReadTimeoutError,
    ResponseStreamingError,
)
from requests_toolbelt import StreamingIterator

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
)
from ralph.backends.mixins import HistoryMixin
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now, parse_bytes_to_dict, parse_dict_to_bytes

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
        DEFAULT_CHUNK_SIZE (str): The default chunk size for reading and writing
            objects.
        LOCALE_ENCODING (str): The encoding used for writing dictionaries to objects.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__S3__"

    ACCESS_KEY_ID: str = None
    SECRET_ACCESS_KEY: str = None
    SESSION_TOKEN: str = None
    ENDPOINT_URL: str = None
    DEFAULT_REGION: str = None
    DEFAULT_BUCKET_NAME: str = None
    DEFAULT_CHUNK_SIZE: int = 4096


class S3DataBackend(HistoryMixin, BaseDataBackend):
    """S3 data backend."""

    name = "s3"
    default_operation_type = BaseOperationType.CREATE
    unsupported_operation_types = {
        BaseOperationType.APPEND,
        BaseOperationType.DELETE,
        BaseOperationType.UPDATE,
    }
    logger = logger
    settings_class = S3DataBackendSettings
    settings: settings_class
    query_class = BaseQuery

    def __init__(self, settings: Union[settings_class, None] = None):
        """Instantiate the AWS S3 client."""
        super().__init__(settings)
        self.default_bucket_name = self.settings.DEFAULT_BUCKET_NAME
        self._client = None

    @property
    def client(self):
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
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List objects for the target bucket.

        Args:
            target (str or None): The target bucket to list from.
                If target is `None`, the `default_bucket_name` is used instead.
            details (bool): Get detailed object information instead of just object name.
            new (bool): Given the history, list only unread files.

        Yields:
            str: The next object name. (If details is False).
            dict: The next object details. (If details is True).

        Raises:
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
            self.logger.error(msg, target, error_msg)
            raise BackendException(msg % (target, error_msg)) from err

    def read(
        self,
        query: Union[str, dict, query_class, None] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Union[int, None] = None,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read an object matching the `query` in the `target` bucket and yields it.

        Args:
            query: (str or BaseQuery): The ID of the object to read.
            target (str or None): The target bucket containing the objects.
                If target is `None`, the `default_bucket` is used instead.
            chunk_size (int or None): The chunk size when reading objects by batch.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
            ignore_errors (bool): If `True`, errors during the read operation
                will be ignored and logged. If `False` (default), a `BackendException`
                will be raised if an error occurs.
            max_statements: The maximum number of statements or chunks to yield.

        Yields:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raises:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid and
                `ignore_errors` is set to `False`.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )

    def _read_bytes(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        bucket, key = self._get_bucket_and_object_key(target, query)
        response = self._get_object(bucket=bucket, key=key)
        try:
            yield from response["Body"].iter_chunks(chunk_size)
        except (ReadTimeoutError, ResponseStreamingError) as error:
            msg = "Failed to read chunk from object %s"
            self.logger.error(msg, key)
            raise BackendException(msg % (key)) from error

        # Archive fetched, add a new entry to the history.
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": bucket + "/" + key,
                "size": response["ContentLength"],
                "timestamp": now(),
            }
        )

    def _read_dicts(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        bucket, key = self._get_bucket_and_object_key(target, query)
        response = self._get_object(bucket=bucket, key=key)
        try:
            lines = response["Body"].iter_lines(chunk_size)
            yield from parse_bytes_to_dict(lines, ignore_errors, self.logger)
        except (ReadTimeoutError, ResponseStreamingError) as error:
            msg = "Failed to read chunk from object %s"
            self.logger.error(msg, key)
            raise BackendException(msg % (query)) from error

        # Archive fetched, add a new entry to the history.
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": bucket + "/" + key,
                "size": response["ContentLength"],
                "timestamp": now(),
            }
        )

    def write(  # pylint: disable=too-many-arguments,useless-parent-delegation
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
    ) -> int:
        """Write `data` records to the `target` bucket and return their count.

        Args:
            data: (Iterable or IOBase): The data to write.
            target (str or None): The target bucket and the target object
                separated by a `/`.
                If target is `None`, the default bucket is used and a random
                (uuid4) object is created.
                If target does not contain a `/`, it is assumed to be the
                target object and the default bucket is used.
            chunk_size (int or None): Ignored.
            ignore_errors (bool): If `True`, errors during the write operation
                are ignored and logged. If `False` (default), a `BackendException`
                is raised if an error occurs.
            operation_type (BaseOperationType or None): The mode of the write
                operation.
                If operation_type is `CREATE` or `INDEX`, the target object is
                expected to be absent. If the target object exists a
                `BackendException` is raised.

        Return:
            int: The number of written objects.

        Raise:
            BackendException: If a failure during the write operation occurs.
            BackendParameterException: If a backend argument value is not valid.
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def close(self) -> None:
        """Close the S3 backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            self.logger.warning("No backend client to close.")
            return

        try:
            self.client.close()
        except ClientError as error:
            msg = "Failed to close S3 backend client: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    def _write_bytes(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[bytes],
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        if not target:
            target = f"{self.default_bucket_name}/{now()}-{uuid4()}"
            msg = "Target not specified; using default bucket with random file name: %s"
            self.logger.info(msg, target)
        elif "/" not in target:
            target = f"{self.default_bucket_name}/{target}"
            msg = "Target bucket not specified; using default bucket: %s"
            self.logger.info(msg, target)

        target_bucket, target_object = target.split("/", 1)

        if target_object in list(self.list(target=target_bucket)):
            msg = "%s already exists and overwrite is not allowed for operation %s"
            self.logger.error(msg, target_object, operation_type)
            raise BackendException(msg % (target_object, operation_type))

        self.logger.info("Creating archive: %s", target_object)

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
        except (ClientError, ParamValidationError, EndpointConnectionError) as exc:
            msg = "Failed to upload %s"
            self.logger.error(msg, target)
            raise BackendException(msg % target) from exc

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

    def _write_dicts(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[dict],
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        bytes_data = parse_dict_to_bytes(
            data, self.settings.LOCALE_ENCODING, ignore_errors, self.logger
        )
        return self._write_bytes(
            bytes_data, target, chunk_size, ignore_errors, operation_type
        )

    def _get_bucket_and_object_key(
        self, target: Union[str, None], query: query_class
    ) -> Tuple[str, str]:
        """Return the validated target bucket and object key."""
        if query.query_string is None:
            msg = "Invalid query. The query should be a valid object name."
            self.logger.error(msg)
            raise BackendParameterException(msg)

        if target is None:
            target = self.default_bucket_name

        return target, query.query_string

    def _get_object(self, bucket: str, key: str) -> dict:
        """Retrieve objects from Amazon S3 wrapping the exception."""
        try:
            return self.client.get_object(Bucket=bucket, Key=key)
        except (ClientError, EndpointConnectionError) as err:
            error_msg = (
                err.response["Error"]["Message"] if hasattr(err, "response") else err
            )
            msg = "Failed to download %s: %s"
            self.logger.error(msg, key, error_msg)
            raise BackendException(msg % (key, error_msg)) from err

    @staticmethod
    def _count(
        statements: Union[Iterable[bytes], Iterable[dict]],
        counter: dict,
    ) -> Iterator:
        """Count the elements in the `statements` Iterable and yield element."""
        for statement in statements:
            counter["count"] += 1
            yield statement
