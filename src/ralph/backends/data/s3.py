"""S3 data backend for Ralph."""

import json
import logging
from io import IOBase
from itertools import chain
from typing import Iterable, Iterator, Union
from uuid import uuid4

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import (
    ClientError,
    ParamValidationError,
    ReadTimeoutError,
    ResponseStreamingError,
)
from botocore.response import StreamingBody
from requests_toolbelt import StreamingIterator

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
    enforce_query_checks,
)
from ralph.backends.mixins import HistoryMixin
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now

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
    LOCALE_ENCODING: str = "utf8"


class S3DataBackend(HistoryMixin, BaseDataBackend):
    """S3 data backend."""

    name = "s3"
    default_operation_type = BaseOperationType.CREATE
    settings_class = S3DataBackendSettings

    def __init__(self, settings: settings_class = None):
        """Instantiate the AWS S3 client."""
        self.settings = settings if settings else self.settings_class()

        self.default_bucket_name = self.settings.DEFAULT_BUCKET_NAME
        self.default_chunk_size = self.settings.DEFAULT_CHUNK_SIZE
        self.locale_encoding = self.settings.LOCALE_ENCODING
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
        except ClientError:
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: str = None, details: bool = False, new: bool = False
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
            logger.error(msg, target, error_msg)
            raise BackendException(msg % (target, error_msg)) from err

    @enforce_query_checks
    def read(
        self,
        *,
        query: Union[str, BaseQuery] = None,
        target: str = None,
        chunk_size: Union[None, int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Read an object matching the `query` in the `target` bucket and yields it.

        Args:
            query: (str or BaseQuery): The ID of the object to read.
            target (str or None): The target bucket containing the objects.
                If target is `None`, the `default_bucket` is used instead.
            chunk_size (int or None): The chunk size for reading objects.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
            ignore_errors (bool): If `True`, errors during the read operation
                will be ignored and logged. If `False` (default), a `BackendException`
                will be raised if an error occurs.

        Yields:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raises:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid and
                `ignore_errors` is set to `False`.
        """
        if query.query_string is None:
            msg = "Invalid query. The query should be a valid object name."
            logger.error(msg)
            raise BackendParameterException(msg)

        if not chunk_size:
            chunk_size = self.default_chunk_size

        if target is None:
            target = self.default_bucket_name

        try:
            response = self.client.get_object(Bucket=target, Key=query.query_string)
        except ClientError as err:
            error_msg = err.response["Error"]["Message"]
            msg = "Failed to download %s: %s"
            logger.error(msg, query.query_string, error_msg)
            if not ignore_errors:
                raise BackendException(msg % (query.query_string, error_msg)) from err

        reader = self._read_raw if raw_output else self._read_dict
        try:
            for chunk in reader(response["Body"], chunk_size, ignore_errors):
                yield chunk
        except (ReadTimeoutError, ResponseStreamingError) as err:
            msg = "Failed to read chunk from object %s"
            logger.error(msg, query.query_string)
            if not ignore_errors:
                raise BackendException(msg % (query.query_string)) from err

        # Archive fetched, add a new entry to the history.
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": target + "/" + query.query_string,
                "size": response["ContentLength"],
                "timestamp": now(),
            }
        )

    def write(  # pylint: disable=too-many-arguments
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[None, str] = None,
        chunk_size: Union[None, int] = None,
        ignore_errors: bool = False,
        operation_type: Union[None, BaseOperationType] = None,
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
        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return 0

        if not operation_type:
            operation_type = self.default_operation_type

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

        if operation_type in [
            BaseOperationType.APPEND,
            BaseOperationType.DELETE,
            BaseOperationType.UPDATE,
        ]:
            msg = "%s operation_type is not allowed."
            logger.error(msg, operation_type.name)
            raise BackendParameterException(msg % operation_type.name)

        if target_object in list(self.list(target=target_bucket)):
            msg = "%s already exists and overwrite is not allowed for operation %s"
            logger.error(msg, target_object, operation_type)
            raise BackendException(msg % (target_object, operation_type))

        logger.info("Creating archive: %s", target_object)

        data = chain((first_record,), data)
        if isinstance(first_record, dict):
            data = self._parse_dict_to_bytes(data, ignore_errors)

        counter = {"count": 0}
        data = self._count(data, counter)

        # Using StreamingIterator from requests-toolbelt but without specifying a size
        # as we will not use it. It implements the `read` method for iterators.
        data = StreamingIterator(0, data)

        try:
            self.client.upload_fileobj(
                Bucket=target_bucket,
                Key=target_object,
                Fileobj=data,
                Config=TransferConfig(multipart_chunksize=chunk_size),
            )
            response = self.client.head_object(Bucket=target_bucket, Key=target_object)
        except (ClientError, ParamValidationError) as exc:
            msg = "Failed to upload %s"
            logger.error(msg, target)
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

    @staticmethod
    def _read_raw(
        obj: StreamingBody, chunk_size: int, _ignore_errors: bool
    ) -> Iterator[bytes]:
        """Read the `object` in chunks of size `chunk_size` and yield them."""
        for chunk in obj.iter_chunks(chunk_size):
            yield chunk

    @staticmethod
    def _read_dict(
        obj: StreamingBody, chunk_size: int, ignore_errors: bool
    ) -> Iterator[dict]:
        """Read the `object` by line and yield JSON parsed dictionaries."""
        for line in obj.iter_lines(chunk_size):
            try:
                yield json.loads(line)
            except (TypeError, json.JSONDecodeError) as err:
                msg = "Raised error: %s"
                logger.error(msg, err)
                if not ignore_errors:
                    raise BackendException(msg % err) from err

    @staticmethod
    def _parse_dict_to_bytes(
        statements: Iterable[dict], ignore_errors: bool
    ) -> Iterator[bytes]:
        """Read the `statements` Iterable and yield bytes."""
        for statement in statements:
            try:
                yield bytes(f"{json.dumps(statement)}\n", encoding="utf-8")
            except TypeError as error:
                msg = "Failed to encode JSON: %s, for document %s"
                logger.error(msg, error, statement)
                if ignore_errors:
                    continue
                raise BackendException(msg % (error, statement)) from error

    @staticmethod
    def _count(
        statements: Union[Iterable[bytes], Iterable[dict]],
        counter: dict,
    ) -> Iterator:
        """Count the elements in the `statements` Iterable and yield element."""
        for statement in statements:
            counter["count"] += 1
            yield statement
