"""Swift storage backend for Ralph"""

import logging
from functools import cached_property
from urllib.parse import urlparse

from swiftclient.service import SwiftService, SwiftUploadObject

from ralph.conf import settings
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now

from ..mixins import HistoryMixin
from .base import BaseStorage

swift_settings = settings.BACKENDS.STORAGE.SWIFT
logger = logging.getLogger(__name__)


class SwiftStorage(
    HistoryMixin, BaseStorage
):  # pylint: disable=too-many-instance-attributes
    """OpenStack's Swift storage backend."""

    name = "swift"

    # pylint: disable=too-many-arguments

    def __init__(
        self,
        os_tenant_id: str = swift_settings.OS_TENANT_ID,
        os_tenant_name: str = swift_settings.OS_TENANT_NAME,
        os_username: str = swift_settings.OS_USERNAME,
        os_password: str = swift_settings.OS_PASSWORD,
        os_region_name: str = swift_settings.OS_REGION_NAME,
        os_storage_url: str = swift_settings.OS_STORAGE_URL,
        os_user_domain_name: str = swift_settings.OS_USER_DOMAIN_NAME,
        os_project_domain_name: str = swift_settings.OS_PROJECT_DOMAIN_NAME,
        os_auth_url: str = swift_settings.OS_AUTH_URL,
        os_identity_api_version: str = swift_settings.OS_IDENTITY_API_VERSION,
    ):
        """Prepares the options for the SwiftService."""

        self.os_tenant_id = os_tenant_id
        self.os_tenant_name = os_tenant_name
        self.os_username = os_username
        self.os_password = os_password
        self.os_region_name = os_region_name
        self.os_user_domain_name = os_user_domain_name
        self.os_project_domain_name = os_project_domain_name
        self.os_auth_url = os_auth_url
        self.os_identity_api_version = os_identity_api_version
        self.container = urlparse(os_storage_url).path.rpartition("/")[-1]
        self.os_storage_url = os_storage_url.removesuffix(f"/{self.container}")

        with SwiftService(self.options) as swift:
            stats = swift.stat()
            if not stats["success"]:
                msg = "Unable to connect to the requested container: %s"
                logger.error(msg, stats["error"])
                raise BackendParameterException(msg % stats["error"])

    @cached_property
    def options(self):
        """Returns the required options for the SwiftService."""

        return {
            "os_auth_url": self.os_auth_url,
            "os_identity_api_version": self.os_identity_api_version,
            "os_password": self.os_password,
            "os_project_domain_name": self.os_project_domain_name,
            "os_region_name": self.os_region_name,
            "os_storage_url": self.os_storage_url,
            "os_tenant_id": self.os_tenant_id,
            "os_tenant_name": self.os_tenant_name,
            "os_username": self.os_username,
            "os_user_domain_name": self.os_user_domain_name,
        }

    def list(self, details=False, new=False):
        """Lists files in the storage backend."""

        archives_to_skip = set()
        if new:
            archives_to_skip = set(self.get_command_history(self.name, "fetch"))
        with SwiftService(self.options) as swift:
            for page in swift.list(self.container):
                if not page["success"]:
                    msg = "Failed to list container %s: %s"
                    logger.error(msg, page["container"], page["error"])
                    raise BackendException(msg % (page["container"], page["error"]))
                for archive in page["listing"]:
                    if new and archive["name"] in archives_to_skip:
                        continue
                    yield archive if details else archive["name"]

    def url(self, name):
        """Gets `name` file absolute URL."""

        # What's the purpose of this function ? Seems not used anywhere.
        return f"{self.options.get('os_storage_url')}/{name}"

    def read(self, name, chunk_size=None):
        """Reads `name` object and yields its content in chunks of (max) 2 ** 16.

        Why chunks of (max) 2 ** 16 ?
            Because SwiftService opens a file to stream the object into:
            See swiftclient.service.py:2082 open(filename, 'rb', DISK_BUFFER)
            Where filename = "/dev/stdout" and DISK_BUFFER = 2 ** 16
        """

        logger.debug("Getting archive: %s", name)

        with SwiftService(self.options) as swift:
            options = {"out_file": "-"}
            download = next(swift.download(self.container, [name], options), {})
        if "contents" not in download:
            msg = "Failed to download %s: %s"
            error = download.get("error", "swift.download did not yield")
            logger.error(msg, download.get("object", name), error)
            raise BackendException(msg % (download.get("object", name), error))
        size = 0
        for chunk in download["contents"]:
            logger.debug("Chunk %s", len(chunk))
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
        """Writes data from `stream` to the `name` target in chunks of (max) 2 ** 16."""

        if not overwrite and name in list(self.list()):
            msg = "%s already exists and overwrite is not allowed"
            logger.error(msg, name)
            raise FileExistsError(msg % name)

        logger.debug("Creating archive: %s", name)

        swift_object = SwiftUploadObject(stream, object_name=name)
        with SwiftService(self.options) as swift:
            for upload in swift.upload(self.container, [swift_object]):
                if not upload["success"]:
                    logger.error(upload["error"])
                    raise BackendException(upload["error"])

        # Archive written, add a new entry to the history
        self.append_to_history(
            {
                "backend": self.name,
                "command": "push",
                "id": name,
                "pushed_at": now(),
            }
        )
