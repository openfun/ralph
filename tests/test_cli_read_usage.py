"""Tests for Ralph cli read usage strings."""

import re
import sys

from click.testing import CliRunner

from ralph.cli import cli

from tests.fixtures.backends import (
    CLICKHOUSE_TEST_HOST,
    ES_TEST_HOSTS,
    MONGO_TEST_COLLECTION,
    MONGO_TEST_CONNECTION_URI,
)


def test_cli_read_command_usage():
    """Test `ralph read` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read BACKEND [OPTIONS] [QUERY]

      Read records matching the QUERY (json or string) from a configured backend.

    Options:
      --help  Show this message and exit.

    Commands:
      async_es     Asynchronous Elasticsearch data backend.
      async_lrs    Asynchronous LRS data backend.
      async_mongo  Asynchronous MongoDB data backend.
      async_ws     Websocket stream backend.
      clickhouse   ClickHouse database backend.
      es           Elasticsearch data backend.
      fs           FileSystem data backend.
      ldp          OVH LDP (Log Data Platform) data backend.
      lrs          LRS data backend.
      mongo        MongoDB data backend.
      s3           S3 data backend.
      swift        SWIFT data backend.
    """
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_async_es_command_usage():
    """Test `ralph read async_es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read async_es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read async_es [OPTIONS] [QUERY]

      Asynchronous Elasticsearch data backend.

      Read documents matching the query in the target index and yield them.

      QUERY: The Elasticsearch query to use when fetching documents.

      QUERY Attributes:

        q (str): The Elastisearch query in the Lucene query string syntax. See
        Elasticsearch search reference for Lucene query syntax:
        https://www.elastic.co/guide/en/elasticsearch/reference/8.9/search-
        search.html#search-api-query-params-q

        query (dict): A search query definition using the Elasticsearch Query DSL.
        See Elasticsearch search reference for query DSL syntax:
        https://www.elastic.co/guide/en/elasticsearch/reference/8.9/search-
        search.html#request-body-search-query

        pit (dict): Limit the search to a point in time (PIT). See ESQueryPit.

        size (int): The maximum number of documents to yield.

        sort (str or list): Specify how to sort search results. Set to `_doc` or
        `_shard_doc` if order doesn't matter. See
        https://www.elastic.co/guide/en/elasticsearch/reference/8.9/sort-search-
        results.html

        search_after (list): Limit search query results to values after a document
        matching the set of sort values in `search_after`. Used for pagination.

        track_total_hits (bool): Number of hits matching the query to count
        accurately. Not used. Always set to `False`.

    Options:
      --allow-yellow-status / --no-allow-yellow-status
                                      Whether to consider Elasticsearch yellow
                                      health status to be ok.  [default: no-allow-
                                      yellow-status]
      --client-options KEY=VALUE,KEY=VALUE
                                      A dictionary of valid options for the
                                      Elasticsearch class initialization.  [default:
                                      ca_certs=None verify_certs=None]
      --default-index TEXT            The default index to use for querying
                                      Elasticsearch.  [default: statements]
      --hosts VALUE1,VALUE2,VALUE3    The comma-separated list of Elasticsearch
                                      nodes to connect to.  [default:
                                      ES_TEST_HOSTS]
      --locale-encoding TEXT          The encoding used for reading/writing
                                      documents.  [default: utf8]
      --point-in-time-keep-alive TEXT
                                      The duration for which Elasticsearch should
                                      keep a point in time alive.  [default: 1m]
      --refresh-after-write TEXT      Whether the Elasticsearch index should be
                                      refreshed after the write operation.
      -p, --prefetch INTEGER          The number of records to prefetch (queue)
                                      while yielding. If `prefetch` is `None` it
                                      defaults to `1`, i.e. no records are
                                      prefetched.
      -m, --max-statements INTEGER    The maximum number of statements to yield. If
                                      `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors             No impact as encoding errors are not expected
                                      in Elasticsearch results.
      -s, --chunk-size INTEGER        The chunk size when reading documents by
                                      batches. If `chunk_size` is `None` it defaults
                                      to `READ_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target Elasticsearch index name to query.
                                      If target is `None`, the `DEFAULT_INDEX` is
                                      used instead.
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_async_lrs_command_usage():
    """Test `ralph read async_lrs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read async_lrs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read async_lrs [OPTIONS] [QUERY]

      Asynchronous LRS data backend.

      Get statements from LRS `target` endpoint.

      QUERY:  The query to select records to read.

      QUERY Attributes:

    Options:
      --base-url TEXT                LRS server URL.  [default: http://0.0.0.0:8100]
      --headers KEY=VALUE,KEY=VALUE  Headers defined for the LRS server connection.
                                     [default: X_EXPERIENCE_API_VERSION='1.0.3'
                                     CONTENT_TYPE='application/json']
      --locale-encoding TEXT         The encoding used for reading statements.
                                     [default: utf8]
      --password TEXT                Basic auth password for LRS authentication.
                                     [default: secret]
      --statements-endpoint TEXT     Default endpoint for LRS statements resource.
                                     [default: /xAPI/statements]
      --status-endpoint TEXT         Endpoint used to check server status.
                                     [default: /__heartbeat__]
      --username TEXT                Basic auth username for LRS authentication.
                                     [default: ralph]
      -p, --prefetch INTEGER         The number of records to prefetch (queue) while
                                     yielding. If `prefetch` is `None` it defaults
                                     to `1` - no records are prefetched.
      -m, --max-statements INTEGER   The maximum number of statements to yield.
      -I, --ignore-errors            If `True`, errors during the read operation are
                                     ignored and logged. If `False` (default), a
                                     `BackendException` is raised if an error
                                     occurs.
      -s, --chunk-size INTEGER       The number of records or bytes to read in one
                                     batch, depending on whether the records are
                                     dictionaries or bytes.  [default: 500]
      -t, --target TEXT              Endpoint from which to read data (e.g.
                                     `/statements`). If target is `None`,
                                     `/xAPI/statements` default endpoint is used.
      --help                         Show this message and exit.
    """
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_async_mongo_command_usage():
    """Test `ralph read async_mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read async_mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read async_mongo [OPTIONS] [QUERY]

      Asynchronous MongoDB data backend.

      Read documents matching the `query` from `target` collection and yield them.

      QUERY: The MongoDB query to use when fetching documents.

      QUERY Attributes:

        filter (dict): A filter query to select which documents to include.

        limit (int): The maximum number of results to return.

        projection (dict): Dictionary specifying the fields to include or exclude.

        sort (list): A list of (key, direction) pairs specifying the sort order.

    Options:
      --client-options KEY=VALUE,KEY=VALUE
                                      A dictionary of MongoDB client options.
                                      [default: document_class=None tz_aware=None]
      --connection-uri TEXT           The MongoDB connection URI.  [default:
                                      MONGO_TEST_CONNECTION_URI]
      --default-collection TEXT       The MongoDB database collection to get objects
                                      from.  [default: MONGO_TEST_COLLECTION]
      --default-database TEXT         The MongoDB database to connect to.  [default:
                                      statements]
      --locale-encoding TEXT          The locale encoding to use when none is
                                      provided.  [default: utf8]
      -p, --prefetch INTEGER          The number of records to prefetch (queue)
                                      while yielding. If `prefetch` is `None` it
                                      defaults to `1`, i.e. no records are
                                      prefetched.
      -m, --max-statements INTEGER    The maximum number of statements to yield. If
                                      `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors             If `True`, encoding errors during the read
                                      operation will be ignored and logged. If
                                      `False` (default), a `BackendException` is
                                      raised on any error.
      -s, --chunk-size INTEGER        The chunk size when reading documents by
                                      batches. If `chunk_size` is `None` it defaults
                                      to `READ_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The MongoDB collection name to query. If
                                      target is `None`, the `DEFAULT_COLLECTION` is
                                      used instead.
      --help                          Show this message and exit.
    """
    output = output.replace("MONGO_TEST_CONNECTION_URI", MONGO_TEST_CONNECTION_URI)
    output = output.replace("MONGO_TEST_COLLECTION", MONGO_TEST_COLLECTION)
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_async_ws_command_usage():
    """Test `ralph read async_ws` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read async_ws --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read async_ws [OPTIONS] [QUERY]

      Websocket stream backend.

      Read records matching the `query` in the `target` container and yield them.

      QUERY: Ignored.

    Options:
      --client-options KEY=VALUE,KEY=VALUE
                                      A dictionary of valid options for the
                                      websocket client connection. See
                                      `WSClientOptions`.  [default:
                                      close_timeout=None compression='deflate'
                                      max_size=1048576 max_queue=32 open_timeout=10
                                      origin=None ping_interval=20 ping_timeout=20
                                      read_limit=65536 USERAGENT_HEADER
                                      websockets/12.0' write_limit=65536]
      --locale-encoding TEXT          [default: utf8]
      --uri TEXT                      The URI to connect to.  [default:
                                      ws://localhost:8765]
      -p, --prefetch INTEGER          The number of records to prefetch (queue)
                                      while yielding. If `prefetch` is `None` it
                                      defaults to `1` - no records are prefetched.
      -m, --max-statements INTEGER    The maximum number of statements to yield.
      -I, --ignore-errors             If `True`, encoding errors during the read
                                      operation will be ignored and logged. If
                                      `False` (default), a `BackendException` is
                                      raised on any error.
      -s, --chunk-size INTEGER        Ignored.  [default: 500]
      -t, --target TEXT               Ignored.
      --help                          Show this message and exit.
    """
    user_agent_header = f" user_agent_header='Python/3.{sys.version_info[1]}"
    if sys.version_info[1] > 9:
        user_agent_header = f"\n{' '*37}{user_agent_header}"
    output = output.replace(" USERAGENT_HEADER", user_agent_header)
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_clickhouse_command_usage():
    """Test `ralph read clickhouse` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read clickhouse --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read clickhouse [OPTIONS] [QUERY]

      ClickHouse database backend.

      Read documents matching the query in the target table and yield them.

      QUERY: The query to use when fetching documents.

      QUERY Attributes:

        select (str or list): Name of the table(s) to query.

        where (str or list): Where expression for filtering the data.

        parameters (dict): Dictionary of substitution values.

        limit (int): Maximum number of rows to return.

        sort (str): Order by expression determining the sorting direction.

        column_oriented (bool): Whether to return the results as a sequence of
        columns rather than a sequence of rows.

    Options:
      --client-options KEY=VALUE,KEY=VALUE
                                      A dictionary of valid options for the
                                      ClickHouse client connection.  [default:
                                      date_time_input_format='best_effort']
      --database TEXT                 ClickHouse database to connect to.  [default:
                                      xapi]
      --event-table-name TEXT         Table where events live.  [default:
                                      xapi_events_all]
      --host TEXT                     ClickHouse server host to connect to.
                                      [default: CLICKHOUSE_TEST_HOST]
      --locale-encoding TEXT          The locale encoding to use when none is
                                      provided.  [default: utf8]
      --password TEXT                 Password for the given ClickHouse username
                                      (optional).
      --port INTEGER                  ClickHouse server port to connect to.
                                      [default: 8123]
      --username TEXT                 ClickHouse username to connect as (optional).
      -m, --max-statements INTEGER    The maximum number of statements to yield. If
                                      `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors             If `True`, encoding errors during the read
                                      operation will be ignored and logged. If
                                      `False` (default), a `BackendException` is
                                      raised on any error.
      -s, --chunk-size INTEGER        The chunk size when reading documents by
                                      batches. If `chunk_size` is `None` it defaults
                                      to `READ_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target table name to query. If target is
                                      `None`, the `EVENT_TABLE_NAME` is used
                                      instead.
      --help                          Show this message and exit.
    """
    output = output.replace("CLICKHOUSE_TEST_HOST", CLICKHOUSE_TEST_HOST)
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_es_command_usage():
    """Test `ralph read es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read es [OPTIONS] [QUERY]

      Elasticsearch data backend.

      Read documents matching the query in the target index and yield them.

      QUERY: The Elasticsearch query to use when fetching documents.

      QUERY Attributes:

        q (str): The Elastisearch query in the Lucene query string syntax. See
        Elasticsearch search reference for Lucene query syntax:
        https://www.elastic.co/guide/en/elasticsearch/reference/8.9/search-
        search.html#search-api-query-params-q

        query (dict): A search query definition using the Elasticsearch Query DSL.
        See Elasticsearch search reference for query DSL syntax:
        https://www.elastic.co/guide/en/elasticsearch/reference/8.9/search-
        search.html#request-body-search-query

        pit (dict): Limit the search to a point in time (PIT). See ESQueryPit.

        size (int): The maximum number of documents to yield.

        sort (str or list): Specify how to sort search results. Set to `_doc` or
        `_shard_doc` if order doesn't matter. See
        https://www.elastic.co/guide/en/elasticsearch/reference/8.9/sort-search-
        results.html

        search_after (list): Limit search query results to values after a document
        matching the set of sort values in `search_after`. Used for pagination.

        track_total_hits (bool): Number of hits matching the query to count
        accurately. Not used. Always set to `False`.

    Options:
      --allow-yellow-status / --no-allow-yellow-status
                                      Whether to consider Elasticsearch yellow
                                      health status to be ok.  [default: no-allow-
                                      yellow-status]
      --client-options KEY=VALUE,KEY=VALUE
                                      A dictionary of valid options for the
                                      Elasticsearch class initialization.  [default:
                                      ca_certs=None verify_certs=None]
      --default-index TEXT            The default index to use for querying
                                      Elasticsearch.  [default: statements]
      --hosts VALUE1,VALUE2,VALUE3    The comma-separated list of Elasticsearch
                                      nodes to connect to.  [default:
                                      ES_TEST_HOSTS]
      --locale-encoding TEXT          The encoding used for reading/writing
                                      documents.  [default: utf8]
      --point-in-time-keep-alive TEXT
                                      The duration for which Elasticsearch should
                                      keep a point in time alive.  [default: 1m]
      --refresh-after-write TEXT      Whether the Elasticsearch index should be
                                      refreshed after the write operation.
      -m, --max-statements INTEGER    The maximum number of statements to yield. If
                                      `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors             No impact as encoding errors are not expected
                                      in Elasticsearch results.
      -s, --chunk-size INTEGER        The chunk size when reading documents by
                                      batches. If `chunk_size` is `None` it defaults
                                      to `READ_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target Elasticsearch index name to query.
                                      If target is `None`, the `DEFAULT_INDEX` is
                                      used instead.
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_fs_command_usage():
    """Test `ralph read fs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read fs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read fs [OPTIONS] [QUERY]

      FileSystem data backend.

      Read files matching the query in the target folder and yield them.

      QUERY: The relative pattern for the files to read.

    Options:
      --default-directory-path PATH  The default target directory path where to
                                     perform list, read and write operations.
                                     [default: .]
      --default-query-string TEXT    The default query string to match files for the
                                     read operation.  [default: *]
      --locale-encoding TEXT         The encoding used for writing dictionaries to
                                     files.  [default: utf8]
      -m, --max-statements INTEGER   The maximum number of statements to yield. If
                                     `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors            If `True`, encoding errors during the read
                                     operation will be ignored and logged. If
                                     `False` (default), a `BackendException` is
                                     raised on any error.
      -s, --chunk-size INTEGER       The chunk size when reading files. If
                                     `chunk_size` is `None` it defaults to
                                     `READ_CHUNK_SIZE`. If `raw_output` is set to
                                     `False`, files are read line by line.
                                     [default: 4096]
      -t, --target TEXT              The target directory path containing the files.
                                     If target is `None`, the
                                     `default_directory_path` is used instead. If
                                     target is a relative path, it is considered to
                                     be relative to the
                                     `default_directory_path`.
      --help                         Show this message and exit.
    """
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_ldp_command_usage():
    """Test `ralph read ldp` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read ldp --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read ldp [OPTIONS] [QUERY]

      OVH LDP (Log Data Platform) data backend.

      Read an archive matching the query in the target stream_id and yield it.

      QUERY: The ID of the archive to read.

    Options:
      --application-key TEXT        The OVH API application key (AK).
      --application-secret TEXT     The OVH API application secret (AS).
      --consumer-key TEXT           The OVH API consumer key (CK).
      --default-stream-id TEXT      The default stream identifier to query.
      --endpoint TEXT               The OVH API endpoint.  [default: ovh-eu]
      --locale-encoding TEXT        [default: utf8]
      --request-timeout TEXT        HTTP request timeout in seconds.
      --service-name TEXT           The default LDP account name.
      -m, --max-statements INTEGER  The maximum number of statements to yield. If
                                    `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors           No impact as no encoding operation is performed.
      -s, --chunk-size INTEGER      The chunk size when reading archives by batch.
                                    If `chunk_size` is `None` it defaults to
                                    `READ_CHUNK_SIZE`.  [default: 4096]
      -t, --target TEXT             The target stream_id containing the archives. If
                                    target is `None`, the `DEFAULT_STREAM_ID` is
                                    used instead.
      --help                        Show this message and exit.
    """
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_lrs_command_usage():
    """Test `ralph read lrs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read lrs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read lrs [OPTIONS] [QUERY]

      LRS data backend.

      Get statements from LRS `target` endpoint.

      QUERY:  The query to select records to read.

      QUERY Attributes:

    Options:
      --base-url TEXT                LRS server URL.  [default: http://0.0.0.0:8100]
      --headers KEY=VALUE,KEY=VALUE  Headers defined for the LRS server connection.
                                     [default: X_EXPERIENCE_API_VERSION='1.0.3'
                                     CONTENT_TYPE='application/json']
      --locale-encoding TEXT         The encoding used for reading statements.
                                     [default: utf8]
      --password TEXT                Basic auth password for LRS authentication.
                                     [default: secret]
      --statements-endpoint TEXT     Default endpoint for LRS statements resource.
                                     [default: /xAPI/statements]
      --status-endpoint TEXT         Endpoint used to check server status.
                                     [default: /__heartbeat__]
      --username TEXT                Basic auth username for LRS authentication.
                                     [default: ralph]
      -m, --max-statements INTEGER   The maximum number of statements to yield.
      -I, --ignore-errors            If `True`, errors during the read operation are
                                     ignored and logged. If `False` (default), a
                                     `BackendException` is raised if an error
                                     occurs.
      -s, --chunk-size INTEGER       The number of records or bytes to read in one
                                     batch, depending on whether the records are
                                     dictionaries or bytes.  [default: 500]
      -t, --target TEXT              Endpoint from which to read data (e.g.
                                     `/statements`). If target is `None`,
                                     `/xAPI/statements` default endpoint is used.
      --help                         Show this message and exit.
    """
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_mongo_command_usage():
    """Test `ralph read mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read mongo [OPTIONS] [QUERY]

      MongoDB data backend.

      Read documents matching the `query` from `target` collection and yield them.

      QUERY: The MongoDB query to use when reading documents.

      QUERY Attributes:

        filter (dict): A filter query to select which documents to include.

        limit (int): The maximum number of results to return.

        projection (dict): Dictionary specifying the fields to include or exclude.

        sort (list): A list of (key, direction) pairs specifying the sort order.

    Options:
      --client-options KEY=VALUE,KEY=VALUE
                                      A dictionary of MongoDB client options.
                                      [default: document_class=None tz_aware=None]
      --connection-uri TEXT           The MongoDB connection URI.  [default:
                                      MONGO_TEST_CONNECTION_URI]
      --default-collection TEXT       The MongoDB database collection to get objects
                                      from.  [default: MONGO_TEST_COLLECTION]
      --default-database TEXT         The MongoDB database to connect to.  [default:
                                      statements]
      --locale-encoding TEXT          The locale encoding to use when none is
                                      provided.  [default: utf8]
      -m, --max-statements INTEGER    The maximum number of statements to yield. If
                                      `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors             If `True`, encoding errors during the read
                                      operation will be ignored and logged. If
                                      `False` (default), a `BackendException` is
                                      raised on any error.
      -s, --chunk-size INTEGER        The chunk size when reading archives by batch.
                                      If `chunk_size` is `None` it defaults to
                                      `READ_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The MongoDB collection name to query. If
                                      target is `None`, the `DEFAULT_COLLECTION` is
                                      used instead.
      --help                          Show this message and exit.
    """
    output = output.replace("MONGO_TEST_CONNECTION_URI", MONGO_TEST_CONNECTION_URI)
    output = output.replace("MONGO_TEST_COLLECTION", MONGO_TEST_COLLECTION)
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_s3_command_usage():
    """Test `ralph read s3` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read s3 --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read s3 [OPTIONS] [QUERY]

      S3 data backend.

      Read an object matching the `query` in the `target` bucket and yield it.

      QUERY: The ID of the object to read.

    Options:
      --access-key-id TEXT          The access key id for the S3 account.
      --default-bucket-name TEXT    The default bucket name targeted.
      --default-region TEXT         The default region used in instantiating the
                                    client.
      --endpoint-url TEXT           The endpoint URL of the S3.
      --locale-encoding TEXT        The encoding used for writing dictionaries to
                                    objects.  [default: utf8]
      --secret-access-key TEXT      The secret key for the S3 account.
      --session-token TEXT          The session token for the S3 account.
      -m, --max-statements INTEGER  The maximum number of statements to yield. If
                                    `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors           If `True`, encoding errors during the read
                                    operation will be ignored and logged. If `False`
                                    (default), a `BackendException` is raised on any
                                    error.
      -s, --chunk-size INTEGER      The number of records or bytes to read in one
                                    batch, depending on whether the records are
                                    dictionaries or bytes. If `chunk_size` is `None`
                                    it defaults to `READ_CHUNK_SIZE`.  [default:
                                    4096]
      -t, --target TEXT             The target bucket containing the object. If
                                    target is `None`, the `default_bucket` is used
                                    instead.
      --help                        Show this message and exit.
    """
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output


def test_cli_read_swift_command_usage():
    """Test `ralph read swift` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "read swift --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph read swift [OPTIONS] [QUERY]

      SWIFT data backend.

      Read objects matching the `query` in the `target` container and yield them.

      QUERY: The query to select objects to read.

    Options:
      --auth-url TEXT               The authentication URL.  [default:
                                    https://auth.cloud.ovh.net/]
      --default-container TEXT      The default target container.
      --identity-api-version TEXT   The keystone API version to authenticate to.
                                    [default: 3]
      --locale-encoding TEXT        The encoding used for reading/writing documents.
                                    [default: utf8]
      --object-storage-url TEXT     The default storage URL.
      --password TEXT               The password of the openstack swift user.
      --project-domain-name TEXT    The project domain name.  [default: Default]
      --region-name TEXT            The region where the container is.
      --tenant-id TEXT              The identifier of the tenant of the container.
      --tenant-name TEXT            The name of the tenant of the container.
      --username TEXT               The name of the openstack swift user.
      --user-domain-name TEXT       The user domain name.  [default: Default]
      -m, --max-statements INTEGER  The maximum number of statements to yield. If
                                    `None` (default) or `0`, there is no maximum.
      -I, --ignore-errors           If `True`, encoding errors during the read
                                    operation will be ignored and logged. If `False`
                                    (default), a `BackendException` is raised on any
                                    error.
      -s, --chunk-size INTEGER      The number of records or bytes to read in one
                                    batch, depending on whether the records are
                                    dictionaries or bytes. If `chunk_size` is `None`
                                    it defaults to `READ_CHUNK_SIZE`.  [default:
                                    4096]
      -t, --target TEXT             The target container name. If `target` is
                                    `None`, a default value is used instead.
      --help                        Show this message and exit.
    """
    assert re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output) == result.output
