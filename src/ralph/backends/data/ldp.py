"""OVH's LDP data backend for Ralph."""

from typing import Iterator, Literal, Optional, Union

import ovh
import requests

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseQuery,
    DataBackendStatus,
    Listable,
    enforce_query_checks,
)
from ralph.backends.data.mixins import HistoryMixin
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now


class LDPDataBackendSettings(BaseDataBackendSettings):
    """OVH LDP (Log Data Platform) data backend default configuration.

    Attributes:
        APPLICATION_KEY (str): The OVH API application key (AK).
        APPLICATION_SECRET (str): The OVH API application secret (AS).
        CONSUMER_KEY (str): The OVH API consumer key (CK).
        DEFAULT_CHUNK_SIZE (str): The default chunk size for reading archives.
        DEFAULT_STREAM_ID (str):  The default stream identifier to query.
        ENDPOINT (str): The OVH API endpoint.
        REQUEST_TIMEOUT (int): HTTP request timeout in seconds.
        SERVICE_NAME (str): The default LDP account name.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__LDP__"

    APPLICATION_KEY: Optional[str] = None
    APPLICATION_SECRET: Optional[str] = None
    CONSUMER_KEY: Optional[str] = None
    DEFAULT_STREAM_ID: Optional[str] = None
    ENDPOINT: Literal[
        "ovh-eu",
        "ovh-us",
        "ovh-ca",
        "kimsufi-eu",
        "kimsufi-ca",
        "soyoustart-eu",
        "soyoustart-ca",
    ] = "ovh-eu"
    REQUEST_TIMEOUT: Optional[int] = None
    SERVICE_NAME: Optional[str] = None
    DEFAULT_CHUNK_SIZE: int = 4096


class LDPDataBackend(
    BaseDataBackend[LDPDataBackendSettings, BaseQuery],
    Listable,
    HistoryMixin,
):
    """OVH LDP (Log Data Platform) data backend."""

    name = "ldp"

    def __init__(self, settings: Optional[LDPDataBackendSettings] = None):
        """Instantiate the OVH LDP client.

        Args:
            settings (LDPDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self.service_name = self.settings.SERVICE_NAME
        self.stream_id = self.settings.DEFAULT_STREAM_ID
        self.timeout = self.settings.REQUEST_TIMEOUT
        self._client = None

    @property
    def client(self) -> ovh.Client:
        """Create an ovh.Client if it doesn't exist."""
        if not self._client:
            self._client = ovh.Client(
                endpoint=self.settings.ENDPOINT,
                application_key=self.settings.APPLICATION_KEY,
                application_secret=self.settings.APPLICATION_SECRET,
                consumer_key=self.settings.CONSUMER_KEY,
            )
        return self._client

    def status(self) -> DataBackendStatus:
        """Check whether the default service_name is accessible."""
        try:
            self.client.get(self._get_archive_endpoint())
        except ovh.exceptions.APIError as error:
            self.logger.error("Failed to connect to the LDP: %s", error)
            return DataBackendStatus.ERROR
        except BackendParameterException:
            return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
        """List archives for a given target stream_id.

        Args:
            target (str or None): The target stream_id where to list the archives.
                If target is `None`, the `DEFAULT_STREAM_ID` is used instead.
            details (bool): Get detailed archive information in addition to archive IDs.
            new (bool): Given the history, list only not already read archives.

        Yield:
            str: If `details` is False.
            dict: If `details` is True.

        Raise:
            BackendParameterException: If the `target` is `None` and no
                `DEFAULT_STREAM_ID` is given.
            BackendException: If a failure during retrieval of archives list occurs.
        """
        list_archives_endpoint = self._get_archive_endpoint(stream_id=target)
        self.logger.info("List archives endpoint: %s", list_archives_endpoint)
        self.logger.info("List archives details: %s", str(details))

        try:
            archives = self.client.get(list_archives_endpoint)
        except ovh.exceptions.APIError as error:
            msg = "Failed to get archives list: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

        self.logger.info("Found %d archives", len(archives))

        if new:
            archives = set(archives) - set(self.get_command_history(self.name, "read"))
            self.logger.debug("New archives: %d", len(archives))

        if not details:
            for archive in archives:
                yield archive

            return

        for archive in archives:
            yield self._details(target, archive)

    @enforce_query_checks
    def read(  # noqa: PLR0913
        self,
        *,
        query: Optional[Union[str, BaseQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = True,
        ignore_errors: bool = False,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
        """Read an archive matching the query in the target stream_id and yield it.

        Args:
            query (str or BaseQuery): The ID of the archive to read.
            target (str or None): The target stream_id containing the archives.
                If target is `None`, the `DEFAULT_STREAM_ID` is used instead.
            chunk_size (int or None): The chunk size when reading archives by batch.
            raw_output (bool): Ignored. Always set to `True`.
            ignore_errors (bool): No impact as no encoding operation is performed.

        Yield:
            bytes: The content of the archive matching the query.

        Raise:
            BackendException: If a failure occurs during LDP connection.
            BackendParameterException: If the `query` argument is not an archive name.
        """
        if query.query_string is None:
            msg = "Invalid query. The query should be a valid archive name"
            self.logger.error(msg)
            raise BackendParameterException(msg)

        if not raw_output or not ignore_errors:
            msg = "The `raw_output` and `ignore_errors` arguments are ignored"
            self.logger.warning(msg)

        target = target if target else self.stream_id
        msg = "Getting archive: %s from stream: %s"
        self.logger.debug(msg, query.query_string, target)

        # Stream response (archive content)
        url = self._url(query.query_string)
        try:
            with requests.get(url, stream=True, timeout=self.timeout) as result:
                result.raise_for_status()
                for chunk in result.iter_content(chunk_size=chunk_size):
                    yield chunk
        except requests.exceptions.HTTPError as error:
            msg = "Failed to read archive %s: %s"
            self.logger.error(msg, query.query_string, error)
            raise BackendException(msg % (query.query_string, error)) from error

        # Get detailed information about the archive to fetch
        details = self._details(target, query.query_string)
        # Archive is supposed to have been fully read, add a new entry to
        # the history.
        self.append_to_history(
            {
                "backend": self.name,
                "command": "read",
                # WARNING: previously only the filename was used as the ID
                # By changing this and prepending the `target` stream_id previously
                # fetched archives will not be marked as read anymore.
                "id": f"{target}/{query.query_string}",
                "filename": details.get("filename"),
                "size": details.get("size"),
                "timestamp": now(),
            }
        )

    def close(self) -> None:
        """LDP data backend has no open connections to close. No action."""
        self._client = None
        self.logger.info("No open connections to close; skipping")

    def _get_archive_endpoint(self, stream_id: Optional[str] = None) -> str:
        """Return OVH's archive endpoint."""
        stream_id = stream_id if stream_id else self.stream_id
        if None in (self.service_name, stream_id):
            msg = "LDPDataBackend requires to set both service_name and stream_id"
            self.logger.error(msg)
            raise BackendParameterException(msg)
        return (
            f"/dbaas/logs/{self.service_name}/output/graylog/stream/{stream_id}/archive"
        )

    def _url(self, name: str) -> str:
        """Get archive absolute URL."""
        download_url_endpoint = f"{self._get_archive_endpoint()}/{name}/url"
        response = self.client.post(download_url_endpoint)
        download_url = response.get("url")
        self.logger.debug("Temporary URL: %s", download_url)
        return download_url

    def _details(self, stream_id: str, name: str) -> Optional[dict]:
        """Return `name` archive details.

        Expected JSON response looks like:

            {
                "archiveId": "5d49d1b3-a3eb-498c-9039-6a482166f888",
                "createdAt": "2020-06-18T04:38:59.436634+02:00",
                "filename": "2020-06-16.gz",
                "md5": "01585b394be0495e38dbb60b20cb40a9",
                "retrievalDelay": 0,
                "retrievalState": "sealed",
                "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
                "size": 67906662,
            }
        """
        return self.client.get(f"{self._get_archive_endpoint(stream_id)}/{name}")
