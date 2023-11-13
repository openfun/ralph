"""Asynchronous Elasticsearch data backend for Ralph."""

from io import IOBase
from itertools import chain
from typing import Iterable, Iterator, Optional, TypeVar, Union

from elasticsearch import ApiError, AsyncElasticsearch, TransportError
from elasticsearch.helpers import BulkIndexError, async_streaming_bulk

from ralph.backends.data.base import (
    AsyncListable,
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseOperationType,
    DataBackendStatus,
    async_enforce_query_checks,
)
from ralph.backends.data.es import ESDataBackend, ESDataBackendSettings, ESQuery
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import async_parse_dict_to_bytes, parse_iterable_to_dict

Settings = TypeVar("Settings", bound=ESDataBackendSettings)


class AsyncESDataBackend(
    BaseAsyncDataBackend[Settings, ESQuery], AsyncWritable, AsyncListable
):
    """Asynchronous Elasticsearch data backend."""

    name = "async_es"

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the asynchronous Elasticsearch client.

        Args:
            settings (ESDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self._client = None

    @property
    def client(self):
        """Create an AsyncElasticsearch client if it doesn't exist."""
        if not self._client:
            self._client = AsyncElasticsearch(
                self.settings.HOSTS, **self.settings.CLIENT_OPTIONS.dict()
            )
        return self._client

    async def status(self) -> DataBackendStatus:
        """Check Elasticsearch cluster connection and status."""
        try:
            await self.client.info()
            cluster_status = await self.client.cat.health()
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

    async def list(
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
            indices = await self.client.indices.get(index=target)
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

    @async_enforce_query_checks
    async def read(  # noqa: PLR0912, PLR0913
        self,
        *,
        query: Optional[Union[str, ESQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Union[None, int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
    ) -> Iterator[Union[bytes, dict]]:
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
            ignore_errors (bool): No impact as encoding errors are not expected in
                Elasticsearch results.

        Yield:
            bytes: The next raw document if `raw_output` is True.
            dict: The next JSON parsed document if `raw_output` is False.

        Raise:
            BackendException: If a failure occurs during Elasticsearch connection.
        """
        if raw_output:
            documents = self.read(
                query=query,
                target=target,
                chunk_size=chunk_size,
                raw_output=False,
                ignore_errors=ignore_errors,
            )
            async for document in async_parse_dict_to_bytes(
                documents, self.settings.LOCALE_ENCODING, ignore_errors, self.logger
            ):
                yield document

            return

        target = target if target else self.settings.DEFAULT_INDEX
        chunk_size = chunk_size if chunk_size else self.settings.DEFAULT_CHUNK_SIZE

        if not query.pit.keep_alive:
            query.pit.keep_alive = self.settings.POINT_IN_TIME_KEEP_ALIVE
        if not query.pit.id:
            try:
                query.pit.id = (
                    await self.client.open_point_in_time(
                        index=target, keep_alive=query.pit.keep_alive
                    )
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
                documents = (await self.client.search(**kwargs))["hits"]["hits"]
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

    async def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[None, str] = None,
        chunk_size: Union[None, int] = None,
        ignore_errors: bool = False,
        operation_type: Union[None, BaseOperationType] = None,
    ) -> int:
        """Write data documents to the target index and return their count.

        Args:
            data: (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target Elasticsearch index name.
                If target is `None`, the `DEFAULT_INDEX` is used instead.
            chunk_size (int or None): The number of documents to write in one batch.
                If chunk_size is `None` it defaults to `DEFAULT_CHUNK_SIZE`.
            ignore_errors (bool): If `True`, errors during decoding, encoding and
                sending batches of documents are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                instead. See `BaseOperationType`.

        Return:
            int: The number of documents written.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If the `operation_type` is `APPEND` as it is not
                supported.
        """
        count = 0
        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            self.logger.info("Data Iterator is empty; skipping write to target.")
            return count
        if not operation_type:
            operation_type = self.default_operation_type
        target = target if target else self.settings.DEFAULT_INDEX
        chunk_size = chunk_size if chunk_size else self.settings.DEFAULT_CHUNK_SIZE
        if operation_type == BaseOperationType.APPEND:
            msg = "Append operation_type is not supported."
            self.logger.error(msg)
            raise BackendParameterException(msg)

        data = chain((first_record,), data)
        if isinstance(first_record, bytes):
            data = parse_iterable_to_dict(data, ignore_errors, self.logger)

        self.logger.debug(
            "Start writing to the %s index (chunk size: %d)", target, chunk_size
        )
        try:
            async for success, action in async_streaming_bulk(
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

    async def close(self) -> None:
        """Close the AsyncElasticsearch client.

        Raise:
            BackendException: If a failure occurs during the close operation.
        """
        if not self._client:
            self.logger.warning("No backend client to close.")
            return

        try:
            await self.client.close()
        except TransportError as error:
            msg = "Failed to close Elasticsearch client: %s"
            self.logger.error(msg, error)
            raise BackendException(msg % error) from error
