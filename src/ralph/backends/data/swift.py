"""Base data backend for Ralph."""

import logging
from functools import cached_property
from io import IOBase
from itertools import chain
from typing import Iterable, Iterator, Optional, Union
from uuid import uuid4

from swiftclient.service import ClientException, Connection

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
    Listable,
    Writable,
    enforce_query_checks,
)
from ralph.backends.mixins import HistoryMixin
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now, parse_dict_to_bytes, parse_iterable_to_dict

logger = logging.getLogger(__name__)


class SwiftDataBackendSettings(BaseDataBackendSettings):
    """Represent the SWIFT data backend default configuration.

    Attributes:
        AUTH_URL (str): The authentication URL.
        USERNAME (str): The name of the openstack swift user.
        PASSWORD (str): The password of the openstack swift user.
        IDENTITY_API_VERSION (str): The keystone API version to authenticate to.
        TENANT_ID (str): The identifier of the tenant of the container.
        TENANT_NAME (str): The name of the tenant of the container.
        PROJECT_DOMAIN_NAME (str): The project domain name.
        REGION_NAME (str): The region where the container is.
        OBJECT_STORAGE_URL (str): The default storage URL.
        USER_DOMAIN_NAME (str): The user domain name.
        DEFAULT_CONTAINER (str): The default target container.
        LOCALE_ENCODING (str): The encoding used for reading/writing documents.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__SWIFT__"

    AUTH_URL: str = "https://auth.cloud.ovh.net/"
    USERNAME: str = None
    PASSWORD: str = None
    IDENTITY_API_VERSION: str = "3"
    TENANT_ID: str = None
    TENANT_NAME: str = None
    PROJECT_DOMAIN_NAME: str = "Default"
    REGION_NAME: str = None
    OBJECT_STORAGE_URL: str = None
    USER_DOMAIN_NAME: str = "Default"
    DEFAULT_CONTAINER: str = None
    LOCALE_ENCODING: str = "utf8"


class SwiftDataBackend(
    BaseDataBackend[SwiftDataBackendSettings, BaseQuery],
    HistoryMixin,
    Writable,
    Listable,
):
    """SWIFT data backend."""

    name = "swift"
    default_operation_type = BaseOperationType.CREATE

    def __init__(self, settings: Optional[SwiftDataBackendSettings] = None):
        """Prepares the options for the SwiftService."""
        super().__init__(settings)
        self.default_container = self.settings.DEFAULT_CONTAINER
        self.locale_encoding = self.settings.LOCALE_ENCODING
        self._connection = None

    @cached_property
    def options(self) -> dict:
        """Return the required options for the Swift Connection."""
        return {
            "tenant_id": self.settings.TENANT_ID,
            "tenant_name": self.settings.TENANT_NAME,
            "project_domain_name": self.settings.PROJECT_DOMAIN_NAME,
            "region_name": self.settings.REGION_NAME,
            "object_storage_url": self.settings.OBJECT_STORAGE_URL,
            "user_domain_name": self.settings.USER_DOMAIN_NAME,
        }

    @property
    def connection(self):
        """Create a Swift Connection if it doesn't exist."""
        if not self._connection:
            self._connection = Connection(
                authurl=self.settings.AUTH_URL,
                user=self.settings.USERNAME,
                key=self.settings.PASSWORD,
                os_options=self.options,
                auth_version=self.settings.IDENTITY_API_VERSION,
            )
        return self._connection

    def status(self) -> DataBackendStatus:
        """Implement data backend checks (e.g. connection, cluster status).

        Return:
            DataBackendStatus: The status of the data backend.
        """
        try:
            self.connection.head_account()
        except ClientException as err:
            msg = "Unable to connect to the Swift account: %s"
            logger.error(msg, err.msg)
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List files for the target container.

        Args:
            target (str or None): The target container to list from.
                If `target` is `None`, the `default_container` will be used.
            details (bool): Get detailed object information instead of just names.
            new (bool): Given the history, list only not already read objects.

        Yield:
            str: The next object path. (If details is False)
            dict: The next object details. (If `details` is True.)

        Raise:
            BackendException: If a failure occurs.
        """
        if target is None:
            target = self.default_container

        archives_to_skip = set()
        if new:
            archives_to_skip = set(self.get_command_history(self.name, "read"))

        try:
            _, objects = self.connection.get_container(
                container=target, full_listing=True
            )
        except ClientException as err:
            msg = "Failed to list container %s: %s"
            logger.error(msg, target, err.msg)
            raise BackendException(msg % (target, err.msg)) from err

        for obj in objects:
            if new and obj in archives_to_skip:
                continue
            yield self._details(target, obj) if details else obj

    @enforce_query_checks
    def read(  # noqa: PLR0913
        self,
        *,
        query: Optional[Union[str, BaseQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = 500,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        """Read objects matching the `query` in the `target` container and yield them.

        Args:
            query: (str or BaseQuery): The query to select objects to read.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            chunk_size (int or None): The number of records or bytes to read in one
                batch, depending on whether the records are dictionaries or bytes.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
                If the objects are dictionaries and `raw_output` is set to `True`, they
                are encoded as JSON.
                If the objects are bytes and `raw_output` is set to `False`, they are
                decoded as JSON by line.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure during the read operation occurs or
                during encoding records and `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        if query.query_string is None:
            msg = "Invalid query. The query should be a valid archive name."
            logger.error(msg)
            raise BackendParameterException(msg)

        target = target if target else self.default_container

        logger.info(
            "Getting object from container: %s (query_string: %s)",
            target,
            query.query_string,
        )

        try:
            resp_headers, content = self.connection.get_object(
                container=target,
                obj=query.query_string,
                resp_chunk_size=chunk_size,
            )
        except ClientException as err:
            msg = "Failed to read %s: %s"
            error = err.msg
            logger.error(msg, query.query_string, error)
            raise BackendException(msg % (query.query_string, error)) from err

        if raw_output:
            while chunk := content.read(chunk_size):
                yield chunk
        else:
            yield from parse_iterable_to_dict(content, ignore_errors, logger)

        # Archive read, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": f"{target}/{query.query_string}",
                "size": resp_headers["Content-Length"],
                "timestamp": now(),
            }
        )

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,  # noqa: ARG002
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` records to the `target` container and returns their count.

        Args:
            data: (Iterable or IOBase): The data to write.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            chunk_size (int or None): Ignored.
            ignore_errors (bool): If `True`, errors during decoding and encoding of
                records are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.

        Return:
            int: The number of written records.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return 0

        data = chain((first_record,), data)
        if isinstance(first_record, dict):
            data = parse_dict_to_bytes(
                data, self.settings.LOCALE_ENCODING, ignore_errors, logger
            )

        counter = {"count": 0}
        data = self._count(data, counter)

        if not operation_type:
            operation_type = self.default_operation_type

        if not target:
            target = f"{self.default_container}/{now()}-{uuid4()}"
            logger.info(
                (
                    "Target not specified; using default container "
                    "with random object name: %s"
                ),
                target,
            )
        elif "/" not in target:
            target = f"{self.default_container}/{target}"
            logger.info(
                "Container not specified; using default container: %s",
                self.default_container,
            )

        target_container, target_object = target.split("/", 1)

        if operation_type in [
            BaseOperationType.APPEND,
            BaseOperationType.DELETE,
            BaseOperationType.UPDATE,
        ]:
            msg = "%s operation_type is not allowed."
            logger.error(msg, operation_type.name)
            raise BackendParameterException(msg % operation_type.name)

        if operation_type in [BaseOperationType.CREATE, BaseOperationType.INDEX]:
            if target_object in list(self.list(target=target_container)):
                msg = "%s already exists and overwrite is not allowed for operation %s"
                logger.error(msg, target_object, operation_type)
                raise BackendException(msg % (target_object, operation_type))

            try:
                self.connection.put_object(
                    container=target_container, obj=target_object, contents=data
                )
                resp = self.connection.head_object(
                    container=target_container, obj=target_object
                )
            except ClientException as err:
                msg = "Failed to write to object %s: %s"
                error = err.msg
                logger.error(msg, target_object, error)
                raise BackendException(msg % (target_object, error)) from err

        count = counter["count"]
        logging.info("Successfully written %s statements to %s", count, target)

        # Archive written, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "action": "write",
                "operation_type": operation_type.value,
                "id": target,
                "size": resp["Content-Length"],
                "timestamp": now(),
            }
        )
        return count

    def close(self) -> None:
        """Close the Swift backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._connection:
            logger.warning("No backend client to close.")
            return

        try:
            self.connection.close()
        except ClientException as error:
            msg = "Failed to close Swift backend client: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    def _details(self, container: str, name: str):
        """Return `name` object details from `container`."""
        try:
            resp = self.connection.head_object(container=container, obj=name)
        except ClientException as err:
            msg = "Unable to retrieve details for object %s: %s"
            logger.error(msg, name, err.msg)
            raise BackendException(msg % (name, err.msg)) from err

        return {
            "name": name,
            "lastModified": resp["Last-Modified"],
            "size": resp["Content-Length"],
        }

    @staticmethod
    def _count(statements: Iterable, counter: dict) -> Iterator:
        """Count the elements in the `statements` Iterable and yield element."""
        for statement in statements:
            yield statement
            counter["count"] += 1
