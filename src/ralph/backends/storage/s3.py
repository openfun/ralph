"""S3 storage backend for Ralph."""

import logging

import boto3
from botocore.exceptions import ClientError, ParamValidationError

from ralph.conf import settings
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now

from ..mixins import HistoryMixin
from .base import BaseStorage

s3_settings = settings.BACKENDS.STORAGE.S3
logger = logging.getLogger(__name__)


class S3Storage(
    HistoryMixin, BaseStorage
):  # pylint: disable=too-many-instance-attributes
    """AWS S3 storage backend."""

    name = "s3"

    # pylint: disable=too-many-arguments

    def __init__(
        self,
        access_key_id: str = s3_settings.ACCESS_KEY_ID,
        secret_access_key: str = s3_settings.SECRET_ACCESS_KEY,
        session_token: str = s3_settings.SESSION_TOKEN,
        default_region: str = s3_settings.DEFAULT_REGION,
        bucket_name: str = s3_settings.BUCKET_NAME,
        endpoint_url: str = s3_settings.ENDPOINT_URL,
    ):
        """Instantiates the AWS S3 client."""
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.session_token = session_token
        self.default_region = default_region
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url

        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            region_name=self.default_region,
            endpoint_url=self.endpoint_url,
        )

        # Check whether bucket exists and is accessible
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as err:
            error_msg = err.response["Error"]["Message"]
            msg = "Unable to connect to the requested bucket: %s"
            logger.error(msg, error_msg)
            raise BackendParameterException(msg % error_msg) from err

    def list(self, details=False, new=False):
        """Lists archives in the storage backend."""
        archives_to_skip = set()
        if new:
            archives_to_skip = set(self.get_command_history(self.name, "fetch"))

        try:
            paginator = self.client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=self.bucket_name)
            for archives in page_iterator:
                if "Contents" not in archives:
                    continue
                for archive in archives["Contents"]:
                    if new and archive["Key"] in archives_to_skip:
                        continue
                    if details:
                        archive["LastModified"] = archive["LastModified"].strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        yield archive
                    else:
                        yield archive["Key"]
        except ClientError as err:
            error_msg = err.response["Error"]["Message"]
            msg = "Failed to list the bucket %s: %s"
            logger.error(msg, self.bucket_name, error_msg)
            raise BackendException(msg % (self.bucket_name, error_msg)) from err

    def url(self, name):
        """Gets `name` file absolute URL."""
        return f"{self.bucket_name}.s3.{self.default_region}.amazonaws.com/{name}"

    def read(self, name, chunk_size: int = 4096):
        """Reads `name` file and yields its content by chunks of a given size."""
        logger.debug("Getting archive: %s", name)

        try:
            obj = self.client.get_object(Bucket=self.bucket_name, Key=name)
        except ClientError as err:
            error_msg = err.response["Error"]["Message"]
            msg = "Failed to download %s: %s"
            logger.error(msg, name, error_msg)
            raise BackendException(msg % (name, error_msg)) from err

        size = 0
        for chunk in obj["Body"].iter_chunks(chunk_size):
            logger.debug("Chunk length %s", len(chunk))
            size += len(chunk)
            yield chunk

        # Archive fetched, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "command": "fetch",
                "id": name,
                "size": size,
                "fetched_at": now(),
            }
        )

    def write(self, stream, name, overwrite=False):
        """Writes data from `stream` to the `name` target."""
        if not overwrite and name in list(self.list()):
            msg = "%s already exists and overwrite is not allowed"
            logger.error(msg, name)
            raise FileExistsError(msg % name)

        logger.debug("Creating archive: %s", name)

        try:
            self.client.upload_fileobj(stream, self.bucket_name, name)
        except (ClientError, ParamValidationError) as exc:
            msg = "Failed to upload"
            logger.error(msg)
            raise BackendException(msg) from exc

        # Archive written, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "command": "push",
                "id": name,
                "pushed_at": now(),
            }
        )
