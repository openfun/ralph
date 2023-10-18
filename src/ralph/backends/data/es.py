"""Elasticsearch data backend for Ralph."""

import logging
from io import IOBase
from pathlib import Path
from typing import Iterable, Iterator, List, Literal, Union

from elasticsearch import ApiError, Elasticsearch, TransportError
from elasticsearch.helpers import BulkIndexError, streaming_bulk
from pydantic import BaseModel

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
)
from ralph.conf import BaseSettingsConfig, ClientOptions, CommaSeparatedTuple
from ralph.exceptions import BackendException
from ralph.utils import parse_bytes_to_dict_new, parse_dict_to_bytes

logger = logging.getLogger(__name__)


class ESClientOptions(ClientOptions):
    """Elasticsearch additional client options."""

    ca_certs: Path = None
    verify_certs: bool = None


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
    DEFAULT_INDEX: str = "statements"
    HOSTS: CommaSeparatedTuple = ("http://localhost:9200",)
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


class ESQuery(BaseQuery):
    """Elasticsearch query model.

    Attributes:
        query (dict): A search query definition using the Elasticsearch Query DSL.
            See Elasticsearch search reference for query DSL syntax:
            https://www.elastic.co/guide/en/elasticsearch/reference/8.9/search-search.html#request-body-search-query
        query_string (str): The Elastisearch query in the Lucene query string syntax.
            See Elasticsearch search reference for Lucene query syntax:
            https://www.elastic.co/guide/en/elasticsearch/reference/8.9/search-search.html#search-api-query-params-q
        pit (dict): Limit the search to a point in time (PIT). See ESQueryPit.
        size (int): The maximum number of documents to yield.
        sort (str or list): Specify how to sort search results. Set to `_doc` or
            `_shard_doc` if order doesn't matter.
            See https://www.elastic.co/guide/en/elasticsearch/reference/8.9/sort-search-results.html
        search_after (list): Limit search query results to values after a document
            matching the set of sort values in `search_after`. Used for pagination.
        track_total_hits (bool): Number of hits matching the query to count accurately.
            Not used. Always set to `False`.
    """  # pylint: disable=line-too-long # noqa: E501

    query: dict = {"match_all": {}}
    pit: ESQueryPit = ESQueryPit()
    size: Union[int, None]
    sort: Union[str, List[dict]] = "_shard_doc"
    search_after: Union[list, None]
    track_total_hits: Literal[False] = False


class ESDataBackend(BaseDataBackend[ESDataBackendSettings, ESQuery]):
    """Elasticsearch data backend."""

    name = "es"
    unsupported_operation_types = {BaseOperationType.APPEND}
    logger = logger

    def __init__(self, settings: Union[ESDataBackendSettings, None] = None):
        """Instantiate the Elasticsearch data backend.

        Args:
            settings (ESDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self._client = None

    @property
    def client(self) -> Elasticsearch:
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
            self.logger.error("Failed to connect to Elasticsearch: %s", error)
            return DataBackendStatus.AWAY

        if "green" in cluster_status:
            return DataBackendStatus.OK

        if "yellow" in cluster_status and self.settings.ALLOW_YELLOW_STATUS:
            self.logger.info("Cluster status is yellow.")
            return DataBackendStatus.OK

        self.logger.error("Cluster status is not green: %s", cluster_status)

        return DataBackendStatus.ERROR

    def list(
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List available Elasticsearch indices, data streams and aliases.

        Args:
            target (str or None): The comma-separated list of data streams, indices,
                and aliases to limit the request. Supports wildcards (*).
                If target is `None`, lists all available indices, data streams and
                    aliases. Equivalent to (`target` = "*").
            details (bool): Get detailed information instead of just names.
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
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error

        if new:
            self.logger.warning("The `new` argument is ignored")

        if details:
            for index, value in indices.items():
                yield {index: value}

            return

        for index in indices:
            yield index

    def read(
        self,
        *,  # We could allow positional arguments once we use validate_backend_query
        query: Union[str, dict, ESQuery, None] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        # max_statements: Union[int, None] = None, (once all backends use the pattern)
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read documents matching the query in the target index and yield them.

        Args:
            query (str or ESQuery): A query in the Lucene query string syntax or a
                dictionary defining a search definition using the Elasticsearch Query
                DSL. The Lucene query overrides the query DSL if present. See ESQuery.
            target (str or None): The target Elasticsearch index name to query.
                If target is `None`, the `DEFAULT_INDEX` is used instead.
            chunk_size (int or None): The chunk size when reading documents by batches.
                If chunk_size is `None` it defaults to `DEFAULT_CHUNK_SIZE`.
            raw_output (bool): Controls whether to yield dictionaries or bytes.
            ignore_errors (bool): Ignored.
            max_statements: The maximum number of statements to yield.

        Yield:
            bytes: The next raw document if `raw_output` is True.
            dict: The next JSON parsed document if `raw_output` is False.

        Raise:
            BackendException: If a failure occurs during Elasticsearch connection.
        """
        if ignore_errors:
            self.logger.warning("The `ignore_errors` argument is ignored")
        yield from super().read(
            query=query,
            target=target,
            chunk_size=chunk_size,
            raw_output=raw_output,
            ignore_errors=ignore_errors,
        )
        # (Replace yield from once all backends use the pattern)
        # yield from super().read(
        #     query, target, chunk_size, raw_output, ignore_errors, max_statements
        # )

    def _read_bytes(
        self, query: ESQuery, target: str, chunk_size: int, ignore_errors: bool
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        locale = self.settings.LOCALE_ENCODING
        statements = self._read_dicts(query, target, chunk_size, ignore_errors)
        yield from parse_dict_to_bytes(statements, locale, ignore_errors, self.logger)

    def _read_dicts(
        self, query: ESQuery, target: str, chunk_size: int, ignore_errors: bool
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        target = target if target else self.settings.DEFAULT_INDEX
        if not query.pit.keep_alive:
            query.pit.keep_alive = self.settings.POINT_IN_TIME_KEEP_ALIVE
        if not query.pit.id:
            try:
                query.pit.id = self.client.open_point_in_time(
                    index=target, keep_alive=query.pit.keep_alive
                )["id"]
            except (ApiError, TransportError, ValueError) as error:
                msg = "Failed to open Elasticsearch point in time: %s"
                self.logger.error(msg, error)
                raise BackendException(msg % error) from error

        limit = query.size
        kwargs = query.dict(exclude={"query_string", "size"})
        if query.query_string:
            kwargs["q"] = query.query_string

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
                self.logger.error(msg, error)
                raise BackendException(msg % error) from error
            count = len(documents)
            if limit:
                limit -= count if chunk_size == count else limit
            query.search_after = None
            if count:
                query.search_after = [str(part) for part in documents[-1]["sort"]]
            kwargs["search_after"] = query.search_after
            for document in documents:
                yield document

    def write(  # pylint: disable=too-many-arguments,useless-parent-delegation
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
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
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_bytes(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[bytes],
        target: str,
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        statements = parse_bytes_to_dict_new(data, ignore_errors, self.logger)
        return self._write_dicts(
            statements, target, chunk_size, ignore_errors, operation_type
        )

    def _write_dicts(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[dict],
        target: str,
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        target = target if target else self.settings.DEFAULT_INDEX
        count = 0
        self.logger.debug(
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
                self.logger.debug("Wrote %d document [action: %s]", success, action)

            self.logger.info("Finished writing %d documents with success", count)
        except (BulkIndexError, ApiError, TransportError) as error:
            msg = "%s %s Total succeeded writes: %s"
            details = getattr(error, "errors", "")
            self.logger.error(msg, error, details, count)
            raise BackendException(msg % (error, details, count)) from error
        return count

    def close(self) -> None:
        """Close the Elasticsearch backend client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            self.logger.warning("No backend client to close.")
            return

        try:
            self.client.close()
        except TransportError as error:
            msg = "Failed to close Elasticsearch client: %s"
            self.logger.error(msg, error)
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
