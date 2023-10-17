"""Swift data backend for Ralph."""

import logging
from functools import cached_property
from io import IOBase
from typing import Iterable, Iterator, Tuple, Union
from uuid import uuid4

from swiftclient.service import ClientException, Connection

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


class SwiftDataBackendSettings(BaseDataBackendSettings):
    """Swift data backend default configuration.

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


class SwiftDataBackend(HistoryMixin, BaseDataBackend):
    """SWIFT data backend."""

    # pylint: disable=too-many-instance-attributes

    name = "swift"
    default_operation_type = BaseOperationType.CREATE
    unsupported_operation_types = {
        BaseOperationType.APPEND,
        BaseOperationType.DELETE,
        BaseOperationType.UPDATE,
    }
    logger = logger
    query_class = BaseQuery
    settings_class = SwiftDataBackendSettings
    settings: settings_class

    def __init__(self, settings: Union[settings_class, None] = None):
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

        Returns:
            DataBackendStatus: The status of the data backend.
        """
        try:
            self.connection.head_account()
        except ClientException as err:
            msg = "Unable to connect to the Swift account: %s"
            self.logger.error(msg, err.msg)
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List files for the target container.

        Args:
            target (str or None): The target container to list from.
                If `target` is `None`, the `default_container` will be used.
            details (bool): Get detailed object information instead of just names.
            new (bool): Given the history, list only not already read objects.

        Yields:
            str: The next object path. (If details is False)
            dict: The next object details. (If `details` is True.)

        Raises:
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
            self.logger.error(msg, target, err.msg)
            raise BackendException(msg % (target, err.msg)) from err

        for obj in objects:
            if new and obj in archives_to_skip:
                continue
            yield self._details(target, obj) if details else obj

    def read(
        self,
        query: Union[str, dict, query_class, None] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = 500,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Union[int, None] = None,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read objects matching the `query` in the `target` container and yields them.

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
            ignore_errors (bool): If `True`, errors during the read operation
                are be ignored and logged. If `False` (default), a `BackendException`
                is raised if an error occurs.
            max_statements: The maximum number of statements or chunks to yield.

        Yields:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raises:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
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
        container, obj = self._get_container_and_object_name(target, query)
        resp_headers, content = self._get_object(container, obj, chunk_size)
        while chunk := content.read(chunk_size):
            yield chunk

        # Archive read, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": f"{container}/{obj}",
                "size": resp_headers["content-length"],
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
        container, obj = self._get_container_and_object_name(target, query)
        resp_headers, content = self._get_object(container, obj, chunk_size)
        yield from parse_bytes_to_dict(content, ignore_errors, self.logger)
        # Archive read, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "action": "read",
                "id": f"{container}/{obj}",
                "size": resp_headers["content-length"],
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
        """Write `data` records to the `target` container and returns their count.

        Args:
            data: (Iterable or IOBase): The data to write.
            target (str or None): The target container name.
                If `target` is `None`, a default value is used instead.
            chunk_size (int or None): Ignored.
            ignore_errors (bool): If `True`, errors during the write operation
                are ignored and logged. If `False` (default), a `BackendException`
                is raised if an error occurs.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.

        Returns:
            int: The number of written records.

        Raises:
            BackendException: If a failure during the write operation occurs and
                `ignore_errors` is set to `False`.
            BackendParameterException: If a backend argument value is not valid.
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

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
            target = f"{self.default_container}/{now()}-{uuid4()}"
            self.logger.info(
                "Target not specified; using default container with random object name:"
                " %s",
                target,
            )

        if "/" not in target:
            target = f"{self.default_container}/{target}"
            msg = "Container not specified; using default container: %s"
            self.logger.info(msg, self.default_container)

        target_container, target_object = target.split("/", 1)
        if target_object in list(self.list(target=target_container)):
            msg = "%s already exists and overwrite is not allowed for operation %s"
            self.logger.error(msg, target_object, operation_type)
            raise BackendException(msg % (target_object, operation_type))

        counter = {"count": 0}
        data = self._count(data, counter)

        try:
            self.connection.put_object(
                container=target_container,
                obj=target_object,
                contents=data,
                chunk_size=chunk_size,
            )
            resp = self.connection.head_object(
                container=target_container, obj=target_object
            )
        except ClientException as error:
            msg = "Failed to write to object %s: %s"
            self.logger.error(msg, target_object, error.msg)
            raise BackendException(msg % (target_object, error.msg)) from error

        msg = "Successfully written %s statements to %s"
        logging.info(msg, counter["count"], target)
        # Archive written, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "action": "write",
                "operation_type": operation_type.value,
                "id": target,
                "size": resp["content-length"],
                "timestamp": now(),
            }
        )
        return counter["count"]

    def _write_dicts(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[dict],
        target: str,
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

    def close(self) -> None:
        """Close the Swift backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._connection:
            self.logger.warning("No backend client to close.")
            return

        try:
            self.connection.close()
        except ClientException as error:
            msg = "Failed to close Swift backend client: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

    def _get_container_and_object_name(
        self, target: Union[str, None], query: query_class
    ) -> Tuple[str, str]:
        """Return the validated target container and object name."""
        if query.query_string is None:
            msg = "Invalid query. The query should be a valid archive name."
            self.logger.error(msg)
            raise BackendParameterException(msg)

        obj = query.query_string
        container = target if target else self.default_container
        msg = "Getting object from container: %s (object: %s)"
        self.logger.info(msg, container, obj)
        return container, obj

    def _get_object(self, container: str, obj: str, chunk_size: int):
        try:
            return self.connection.get_object(container, obj, chunk_size)
        except ClientException as error:
            msg = "Failed to read %s: %s"
            self.logger.error(msg, obj, error.msg)
            raise BackendException(msg % (obj, error.msg)) from error

    def _details(self, container: str, name: str):
        """Return `name` object details from `container`."""
        try:
            resp = self.connection.head_object(container=container, obj=name)
        except ClientException as err:
            msg = "Unable to retrieve details for object %s: %s"
            self.logger.error(msg, name, err.msg)
            raise BackendException(msg % (name, err.msg)) from err

        return {
            "name": name,
            "lastModified": resp["last-modified"],
            "size": resp["content-length"],
        }

    @staticmethod
    def _count(
        statements: Union[Iterable[bytes], Iterable[dict]],
        counter: dict,
    ) -> Iterator:
        """Count the elements in the `statements` Iterable and yield element."""
        for statement in statements:
            counter["count"] += 1
            yield statement
