"""Swift storage backend for Ralph"""

import logging
import sys
from functools import cached_property
from urllib.parse import urlparse

from swiftclient.service import SwiftService, SwiftUploadObject

from ralph.defaults import (
    SWIFT_OS_AUTH_URL,
    SWIFT_OS_IDENTITY_API_VERSION,
    SWIFT_OS_PROJECT_DOMAIN_NAME,
    SWIFT_OS_USER_DOMAIN_NAME,
)
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now

from ..mixins import HistoryMixin
from .base import BaseStorage

logger = logging.getLogger(__name__)


class SwiftStorage(
    HistoryMixin, BaseStorage
):  # pylint: disable=too-many-instance-attributes
    """OpenStack's Swift storage backend"""

    name = "swift"

    # pylint: disable=too-many-arguments

    def __init__(
        self,
        os_tenant_id,
        os_tenant_name,
        os_username,
        os_password,
        os_region_name,
        os_storage_url,
        os_user_domain_name=SWIFT_OS_USER_DOMAIN_NAME,
        os_project_domain_name=SWIFT_OS_PROJECT_DOMAIN_NAME,
        os_auth_url=SWIFT_OS_AUTH_URL,
        os_identity_api_version=SWIFT_OS_IDENTITY_API_VERSION,
    ):
        """Setup options for the SwiftService"""

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
        """Returns the required options for the SwiftService"""

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
        """List files in the storage backend"""

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
        """Get `name` file absolute URL"""

        # What's the purpose of this function ? Seems not used anywhere.
        return f"{self.options.get('os_storage_url')}/{name}"

    def read(self, name, chunk_size=None):
        """Read `name` object and stream its content in chunks of (max) 2 ** 16

        Why chunks of (max) 2 ** 16 ?
            Because SwiftService opens a file to stream the object into:
            See swiftclient.service.py:2082 open(filename, 'rb', DISK_BUFFER)
            Where filename = "/dev/stdout" and DISK_BUFFER = 2 ** 16
        """

        logger.debug("Getting archive: %s", name)

        with SwiftService(self.options) as swift:
            download = next(swift.download(self.container, [name], {"out_file": "-"}))
        if "contents" not in download:
            msg = "Failed to download %s: %s"
            logger.error(msg, download["object"], download["error"])
            raise BackendException(msg % (download["object"], download["error"]))
        size = 0
        for chunk in download["contents"]:
            logger.debug("Chunk %s", len(chunk))
            size += len(chunk)
            sys.stdout.buffer.write(chunk)

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

    def write(self, name, chunk_size=None, overwrite=False):
        """Write content to the `name` target in chunks of (max) 2 ** 16"""

        if not overwrite and name in list(self.list()):
            msg = "%s already exists and overwrite is not allowed"
            logger.error(msg, name)
            raise FileExistsError(msg % name)

        logger.debug("Creating archive: %s", name)

        swift_object = SwiftUploadObject(sys.stdin.buffer, object_name=name)
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
