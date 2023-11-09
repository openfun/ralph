"""Elasticsearch data backend for Ralph."""

import logging
from io import IOBase
from itertools import chain
from pathlib import Path
from typing import Iterable, Iterator, List, Literal, Optional, Union

from elasticsearch import ApiError, Elasticsearch, TransportError
from elasticsearch.helpers import BulkIndexError, streaming_bulk
from pydantic import BaseModel

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    DataBackendStatus,
    Listable,
    Writable,
)
from ralph.conf import BaseSettingsConfig, ClientOptions, CommaSeparatedTuple
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import parse_bytes_to_dict, read_raw

logger = logging.getLogger(__name__)


class ESClientOptions(ClientOptions):
    """Elasticsearch additional client options."""

    ca_certs: Optional[Path] = None
    verify_certs: Optional[bool] = None


class ESDataBackendSettings(BaseDataBackendSettings):
    """Elasticsearch data backend default configuration.

    Attributes:
        ALLOW_YELLOW_STATUS (bool): Whether to consider Elasticsearch yellow health
            status to be ok.
        CLIENT_OPTIONS (dict): A dictionary of valid options for the Elasticsearch class
            initialization.
        DEFAULT_CHUNK_SIZE (int): The default chunk size for reading batches of
            documents.
        DEFAULT_INDEX (str): The default index to use for querying Elasticsearch.
        HOSTS (str or tuple): The comma separated list of Elasticsearch nodes to
            connect to.
        LOCALE_ENCODING (str): The encoding used for reading/writing documents.
        POINT_IN_TIME_KEEP_ALIVE (str): The duration for which Elasticsearch should
            keep a point in time alive.
        REFRESH_AFTER_WRITE (str or bool): Whether the Elasticsearch index should be
            refreshed after the write operation.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__ES__"

    ALLOW_YELLOW_STATUS: bool = False
    CLIENT_OPTIONS: ESClientOptions = ESClientOptions()
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_INDEX: str = "statements"
    HOSTS: CommaSeparatedTuple = ("http://localhost:9200",)
    LOCALE_ENCODING: str = "utf8"
    POINT_IN_TIME_KEEP_ALIVE: str = "1m"
    REFRESH_AFTER_WRITE: Union[Literal["false", "true", "wait_for"], bool, str, None]


class ESQueryPit(BaseModel):
    """Elasticsearch point in time (pit) query configuration.

    Attributes:
        id (str): Context identifier of the Elasticsearch point in time.
        keep_alive (str): The duration for which Elasticsearch should keep the point in
            time alive.
    """

    id: Union[str, None]
    keep_alive: Union[str, None]


class ESQuery(BaseModel):
    """Elasticsearch query model.

    Attributes:
        query (dict): A search query definition using the Elasticsearch Query DSL.
            See Elasticsearch search reference for query DSL syntax:
            https://www.elastic.co/guide/en/elasticsearch/reference/8.9/search-search.html#request-body-search-query
        pit (dict): Limit the search to a point in time (PIT). See ESQueryPit.
        size (int): The maximum number of documents to yield.
        sort (str or list): Specify how to sort search results. Set to `_doc` or
            `_shard_doc` if order doesn't matter.
            See https://www.elastic.co/guide/en/elasticsearch/reference/8.9/sort-search-results.html
        search_after (list): Limit search query results to values after a document
            matching the set of sort values in `search_after`. Used for pagination.
        track_total_hits (bool): Number of hits matching the query to count accurately.
            Not used. Always set to `False`.
    """

    query: dict = {"match_all": {}}
    pit: ESQueryPit = ESQueryPit()
    size: Union[int, None]
    sort: Union[str, List[dict]] = "_shard_doc"
    search_after: Union[list, None]
    track_total_hits: Literal[False] = False


class ESDataBackend(BaseDataBackend, Writable, Listable):
    """Elasticsearch data backend."""

    name = "es"
    query_class = ESQuery
    settings_class = ESDataBackendSettings

    def __init__(self, settings: Optional[ESDataBackendSettings] = None):
        """Instantiate the Elasticsearch data backend.

        Args:
            settings (ESDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        self.settings = settings if settings else self.settings_class()
        self._client = None

    @property
    def client(self):
        """Create an Elasticsearch client if it doesn't exist."""
        if not self._client:
            self._client = Elasticsearch(
                self.settings.HOSTS, **self.settings.CLIENT_OPTIONS.dict()
            )
        return self._client

    def status(self) -> DataBackendStatus:
        """Check Elasticsearch cluster connection and status."""
        try:
            self.client.info()
            cluster_status = self.client.cat.health()
        except TransportError as error:
            logger.error("Failed to connect to Elasticsearch: %s", error)
            return DataBackendStatus.AWAY

        if "green" in cluster_status:
            return DataBackendStatus.OK

        if "yellow" in cluster_status and self.settings.ALLOW_YELLOW_STATUS:
            logger.info("Cluster status is yellow.")
            return DataBackendStatus.OK

        logger.error("Cluster status is not green: %s", cluster_status)

        return DataBackendStatus.ERROR

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List available Elasticsearch indices, data streams and aliases.

        Args:
            target (str or None): The comma-separated list of data streams, indices,
                and aliases to limit the request. Supports wildcards (*).
                If target is `None`, lists all available indices, data streams and
                    aliases. Equivalent to (`target` = "*").
            details (bool): Get detailed informations instead of just names.
            new (bool): Ignored.

        Yield:
            str: The next index, data stream or alias name. (If `details` is False).
            dict: The next index, data stream or alias details. (If `details` is True).

        Raise:
            BackendException: If a failure during indices retrieval occurs.
        """
        target = target if target else "*"
        try:
            indices = self.client.indices.get(index=target)
        except (ApiError, TransportError) as error:
            msg = "Failed to read indices: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

        if new:
            logger.warning("The `new` argument is ignored")

        if details:
            for index, value in indices.items():
                yield {index: value}

            return

        for index in indices:
            yield index

    def read(  # noqa: PLR0912, PLR0913
        self,
        *,
        query: Optional[ESQuery] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments,too-many-branches
        """Read documents matching the query in the target index and yield them.

        Args:
            query (ESQuery): A query in the Lucene query string syntax or a
                dictionary defining a search definition using the Elasticsearch Query
                DSL. The Lucene query overrides the query DSL if present. See ESQuery.
            target (str or None): The target Elasticsearch index name to query.
                If target is `None`, the `DEFAULT_INDEX` is used instead.
            chunk_size (int or None): The chunk size when reading documents by batches.
                If chunk_size is `None` it defaults to `DEFAULT_CHUNK_SIZE`.
            raw_output (bool): Controls whether to yield dictionaries or bytes.
            ignore_errors (bool): Ignored.

        Yield:
            bytes: The next raw document if `raw_output` is True.
            dict: The next JSON parsed document if `raw_output` is False.

        Raise:
            BackendException: If a failure occurs during Elasticsearch connection.
        """
        target = target if target else self.settings.DEFAULT_INDEX
        chunk_size = chunk_size if chunk_size else self.settings.DEFAULT_CHUNK_SIZE
        if ignore_errors:
            logger.warning("The `ignore_errors` argument is ignored")

        if query is None:
            query = self.query_class()

        if not query.pit.keep_alive:
            query.pit.keep_alive = self.settings.POINT_IN_TIME_KEEP_ALIVE
        if not query.pit.id:
            try:
                query.pit.id = self.client.open_point_in_time(
                    index=target, keep_alive=query.pit.keep_alive
                )["id"]
            except (ApiError, TransportError, ValueError) as error:
                msg = "Failed to open Elasticsearch point in time: %s"
                logger.error(msg, error)
                raise BackendException(msg % error) from error

        limit = query.size
        kwargs = query.dict(exclude={"size"})

        count = chunk_size
        # The first condition is set to comprise either limit as None
        # (when the backend query does not have `size` parameter),
        # or limit with a positive value.
        while limit != 0 and chunk_size == count:
            kwargs["size"] = limit if limit and limit < chunk_size else chunk_size
            try:
                documents = self.client.search(**kwargs)["hits"]["hits"]
            except (ApiError, TransportError, TypeError) as error:
                msg = "Failed to execute Elasticsearch query: %s"
                logger.error(msg, error)
                raise BackendException(msg % error) from error
            count = len(documents)
            if limit:
                limit -= count if chunk_size == count else limit
            query.search_after = None
            if count:
                query.search_after = [str(part) for part in documents[-1]["sort"]]
            kwargs["search_after"] = query.search_after
            if raw_output:
                documents = read_raw(
                    documents, self.settings.LOCALE_ENCODING, ignore_errors, logger
                )
            for document in documents:
                yield document

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write data documents to the target index and return their count.

        Args:
            data: (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target Elasticsearch index name.
                If target is `None`, the `DEFAULT_INDEX` is used instead.
            chunk_size (int or None): The number of documents to write in one batch.
                If chunk_size is `None` it defaults to `DEFAULT_CHUNK_SIZE`.
            ignore_errors (bool): If `True`, errors during the write operation
                will be ignored and logged. If `False` (default), a `BackendException`
                will be raised if an error occurs.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.

        Return:
            int: The number of documents written.

        Raise:
            BackendException: If a failure occurs while writing to Elasticsearch or
                during document decoding and `ignore_errors` is set to `False`.
            BackendParameterException: If the `operation_type` is `APPEND` as it is not
                supported.
        """
        count = 0
        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return count
        if not operation_type:
            operation_type = self.default_operation_type
        target = target if target else self.settings.DEFAULT_INDEX
        chunk_size = chunk_size if chunk_size else self.settings.DEFAULT_CHUNK_SIZE
        if operation_type == BaseOperationType.APPEND:
            msg = "Append operation_type is not supported."
            logger.error(msg)
            raise BackendParameterException(msg)

        data = chain((first_record,), data)
        if isinstance(first_record, bytes):
            data = parse_bytes_to_dict(data, ignore_errors, logger)

        logger.debug(
            "Start writing to the %s index (chunk size: %d)", target, chunk_size
        )
        try:
            for success, action in streaming_bulk(
                client=self.client,
                actions=ESDataBackend.to_documents(data, target, operation_type),
                chunk_size=chunk_size,
                raise_on_error=(not ignore_errors),
                refresh=self.settings.REFRESH_AFTER_WRITE,
            ):
                count += success
                logger.debug("Wrote %d document [action: %s]", success, action)

            logger.info("Finished writing %d documents with success", count)
        except (BulkIndexError, ApiError, TransportError) as error:
            msg = "%s %s Total succeeded writes: %s"
            details = getattr(error, "errors", "")
            logger.error(msg, error, details, count)
            raise BackendException(msg % (error, details, count)) from error
        return count

    def close(self) -> None:
        """Close the Elasticsearch backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            logger.warning("No backend client to close.")
            return

        try:
            self.client.close()
        except TransportError as error:
            msg = "Failed to close Elasticsearch client: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    @staticmethod
    def to_documents(
        data: Iterable[dict],
        target: str,
        operation_type: BaseOperationType,
    ) -> Iterator[dict]:
        """Convert dictionaries from `data` to ES documents and yield them."""
        if operation_type == BaseOperationType.UPDATE:
            for item in data:
                yield {
                    "_index": target,
                    "_id": item.get("id", None),
                    "_op_type": operation_type.value,
                    "doc": item,
                }
        elif operation_type in (BaseOperationType.CREATE, BaseOperationType.INDEX):
            for item in data:
                yield {
                    "_index": target,
                    "_id": item.get("id", None),
                    "_op_type": operation_type.value,
                    "_source": item,
                }
        else:
            # operation_type == BaseOperationType.DELETE (by exclusion)
            for item in data:
                yield {
                    "_index": target,
                    "_id": item.get("id", None),
                    "_op_type": operation_type.value,
                }
