"""Tests for Ralph cli read usage strings."""

import re

from click.testing import CliRunner

from ralph.cli import cli

from tests.fixtures.backends import (
    CLICKHOUSE_TEST_HOST,
    ES_TEST_HOSTS,
    MONGO_TEST_COLLECTION,
    MONGO_TEST_CONNECTION_URI,
)


def test_cli_write_command_usage():
    """Test `ralph write` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write BACKEND [OPTIONS]

      Write data to a configured backend.

    Options:
      --help  Show this message and exit.

    Commands:
      async_es     Asynchronous Elasticsearch data backend.
      async_lrs    Asynchronous LRS data backend.
      async_mongo  Asynchronous MongoDB data backend.
      clickhouse   ClickHouse database backend.
      es           Elasticsearch data backend.
      fs           FileSystem data backend.
      lrs          LRS data backend.
      mongo        MongoDB data backend.
      s3           S3 data backend.
      swift        SWIFT data backend.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_async_es_command_usage():
    """Test the `ralph write async_es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write async_es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write async_es [OPTIONS]

      Asynchronous Elasticsearch data backend.

      Write data documents to the target index and return their count.

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
      -c, --concurrency INTEGER       The number of chunks to write concurrently. If
                                      `None` it defaults to `1`.
      -o, --operation-type OP_TYPE    The mode of the write operation. If
                                      `operation_type` is `None`, the
                                      `default_operation_type` is used instead. See
                                      `BaseOperationType`.  [default: index]
      -I, --ignore-errors             If `True`, errors during decoding, encoding
                                      and sending batches of documents are ignored
                                      and logged. If `False` (default), a
                                      `BackendException` is raised on any error.
      -s, --chunk-size INTEGER        The number of documents to write in one batch.
                                      If `chunk_size` is `None` it defaults to
                                      `WRITE_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target Elasticsearch index name. If target
                                      is `None`, the `DEFAULT_INDEX` is used
                                      instead.
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_async_lrs_command_usage():
    """Test the `ralph write async_lrs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write async_lrs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write async_lrs [OPTIONS]

      Asynchronous LRS data backend.

      Write `data` records to the `target` endpoint and return their count.

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
      -c, --concurrency INTEGER      The number of chunks to write concurrently. If
                                     `None` it defaults to `1`.
      -o, --operation-type OP_TYPE   The mode of the write operation. If
                                     `operation_type` is `None`, the
                                     `default_operation_type` is used instead. See
                                     `BaseOperationType`.  [default: create]
      -I, --ignore-errors            If `True`, errors during the write operation
                                     are ignored and logged. If `False` (default), a
                                     `BackendException` is raised if an error
                                     occurs.
      -s, --chunk-size INTEGER       The number of records or bytes to write in one
                                     batch, depending on whether `data` contains
                                     dictionaries or bytes. If `chunk_size` is
                                     `None`, a default value is used instead.
                                     [default: 500]
      -t, --target TEXT              Endpoint in which to write data (e.g.
                                     `/statements`). If `target` is `None`,
                                     `/xAPI/statements` default endpoint is used.
      --help                         Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_async_mongo_command_usage():
    """Test the `ralph write async_mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write async_mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write async_mongo [OPTIONS]

      Asynchronous MongoDB data backend.

      Write data documents to the target collection and return their count.

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
      -c, --concurrency INTEGER       The number of chunks to write concurrently. If
                                      `None` it defaults to `1`.
      -o, --operation-type OP_TYPE    The mode of the write operation. If
                                      `operation_type` is `None`, the
                                      `default_operation_type` is used instead. See
                                      `BaseOperationType`.  [default: index]
      -I, --ignore-errors             If `True`, errors during decoding, encoding
                                      and sending batches of documents are ignored
                                      and logged. If `False` (default), a
                                      `BackendException` is raised on any error.
      -s, --chunk-size INTEGER        The number of documents to write in one batch.
                                      If `chunk_size` is `None` it defaults to
                                      `WRITE_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target MongoDB collection name.
      --help                          Show this message and exit.
    """
    output = output.replace("MONGO_TEST_CONNECTION_URI", MONGO_TEST_CONNECTION_URI)
    output = output.replace("MONGO_TEST_COLLECTION", MONGO_TEST_COLLECTION)
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_clickhouse_command_usage():
    """Test the `ralph write clickhouse` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write clickhouse --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write clickhouse [OPTIONS]

      ClickHouse database backend.

      Write `data` documents to the `target` table and return their count.

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
      -o, --operation-type OP_TYPE    The mode of the write operation. If
                                      `operation_type` is `None`, the
                                      `default_operation_type` is used instead. See
                                      `BaseOperationType`.  [default: create]
      -I, --ignore-errors             If `True`, errors during decoding, encoding
                                      and sending batches of documents are ignored
                                      and logged. If `False` (default), a
                                      `BackendException` is raised on any error.
      -s, --chunk-size INTEGER        The number of documents to write in one batch.
                                      If `chunk_size` is `None` it defaults to
                                      `WRITE_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target table name. If target is `None`,
                                      the `EVENT_TABLE_NAME` is used instead.
      --help                          Show this message and exit.
    """
    output = output.replace("CLICKHOUSE_TEST_HOST", CLICKHOUSE_TEST_HOST)
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_es_command_usage():
    """Test the `ralph write es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write es [OPTIONS]

      Elasticsearch data backend.

      Write data documents to the target index and return their count.

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
      -o, --operation-type OP_TYPE    The mode of the write operation. If
                                      `operation_type` is `None`, the
                                      `default_operation_type` is used instead. See
                                      `BaseOperationType`.  [default: index]
      -I, --ignore-errors             If `True`, errors during decoding, encoding
                                      and sending batches of documents are ignored
                                      and logged. If `False` (default), a
                                      `BackendException` is raised on any error.
      -s, --chunk-size INTEGER        The number of documents to write in one batch.
                                      If `chunk_size` is `None` it defaults to
                                      `WRITE_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target Elasticsearch index name. If target
                                      is `None`, the `DEFAULT_INDEX` is used
                                      instead.
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_fs_command_usage():
    """Test the `ralph write fs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write fs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write fs [OPTIONS]

      FileSystem data backend.

      Write data records to the target file and return their count.

    Options:
      --default-directory-path PATH  The default target directory path where to
                                     perform list, read and write operations.
                                     [default: .]
      --default-query-string TEXT    The default query string to match files for the
                                     read operation.  [default: *]
      --locale-encoding TEXT         The encoding used for writing dictionaries to
                                     files.  [default: utf8]
      -o, --operation-type OP_TYPE   The mode of the write operation. If
                                     operation_type is `CREATE` or `INDEX`, the
                                     target file is expected to     be absent. If
                                     the target file exists a `FileExistsError` is
                                     raised. If operation_type is `UPDATE`, the
                                     target file is overwritten. If operation_type
                                     is `APPEND`, the data is appended to the
                                     end of the target file.  [default: create]
      -I, --ignore-errors            If `True`, errors during decoding and encoding
                                     of records are ignored and logged. If `False`
                                     (default), a `BackendException` is raised on
                                     any error.
      -s, --chunk-size INTEGER       Ignored.  [default: 4096]
      -t, --target TEXT              The target file path. If target is a relative
                                     path, it is considered to be relative to the
                                     `default_directory_path`. If target is `None`,
                                     a random (uuid4) file is created in the
                                     `default_directory_path` and used as the target
                                     instead.
      --help                         Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_lrs_command_usage():
    """Test the `ralph write lrs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write lrs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write lrs [OPTIONS]

      LRS data backend.

      Write `data` records to the `target` endpoint and return their count.

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
      -o, --operation-type OP_TYPE   The mode of the write operation. If
                                     `operation_type` is `None`, the
                                     `default_operation_type` is used instead. See
                                     `BaseOperationType`.  [default: create]
      -I, --ignore-errors            If `True`, errors during the write operation
                                     are ignored and logged. If `False` (default), a
                                     `BackendException` is raised if an error
                                     occurs.
      -s, --chunk-size INTEGER       The number of records or bytes to write in one
                                     batch, depending on whether `data` contains
                                     dictionaries or bytes. If `chunk_size` is
                                     `None`, a default value is used instead.
                                     [default: 500]
      -t, --target TEXT              Endpoint in which to write data (e.g.
                                     `/statements`). If `target` is `None`,
                                     `/xAPI/statements` default endpoint is used.
      --help                         Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_mongo_command_usage():
    """Test the `ralph write mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write mongo [OPTIONS]

      MongoDB data backend.

      Write `data` documents to the `target` collection and return their count.

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
      -o, --operation-type OP_TYPE    The mode of the write operation. If
                                      `operation_type` is `None`, the
                                      `default_operation_type` is used instead. See
                                      `BaseOperationType`.  [default: index]
      -I, --ignore-errors              If `True`, errors during decoding, encoding
                                       and sending batches of documents are ignored
                                       and logged. If `False` (default), a
                                       `BackendException` is raised on any error.
      -s, --chunk-size INTEGER        The number of documents to write in one batch.
                                      If `chunk_size` is `None` it defaults to
                                      `WRITE_CHUNK_SIZE`.  [default: 500]
      -t, --target TEXT               The target MongoDB collection name.
      --help                          Show this message and exit.
    """
    output = output.replace("MONGO_TEST_CONNECTION_URI", MONGO_TEST_CONNECTION_URI)
    output = output.replace("MONGO_TEST_COLLECTION", MONGO_TEST_COLLECTION)
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_s3_command_usage():
    """Test the `ralph write s3` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write s3 --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write s3 [OPTIONS]

      S3 data backend.

      Write `data` records to the `target` bucket and return their count.

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
      -o, --operation-type OP_TYPE  The mode of the write operation. If
                                    operation_type is `CREATE` or `INDEX`, the
                                    target object is expected to be absent. If the
                                    target object exists a `BackendException` is
                                    raised.  [default: create]
      -I, --ignore-errors           If `True`, errors during decoding and encoding
                                    of records are ignored and logged. If `False`
                                    (default), a `BackendException` is raised on any
                                    error.
      -s, --chunk-size INTEGER      The chunk size when writing objects by batch. If
                                    `chunk_size` is `None` it defaults to
                                    `WRITE_CHUNK_SIZE`.  [default: 4096]
      -t, --target TEXT             The target bucket and the target object
                                    separated by a `/`. If target is `None`, the
                                    default bucket is used and a random (uuid4)
                                    object is created. If target does not contain a
                                    `/`, it is assumed to be the target object and
                                    the default bucket is used.
      --help                        Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_write_swift_command_usage():
    """Test the `ralph write swift` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "write swift --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph write swift [OPTIONS]

      SWIFT data backend.

      Write `data` records to the `target` container and returns their count.

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
      -o, --operation-type OP_TYPE  The mode of the write operation. If
                                    `operation_type` is `None`, the
                                    `default_operation_type` is used instead. See
                                    `BaseOperationType`.  [default: create]
      -I, --ignore-errors           If `True`, errors during decoding and encoding
                                    of records are ignored and logged. If `False`
                                    (default), a `BackendException` is raised on any
                                    error.
      -s, --chunk-size INTEGER      The chunk size when writing objects by batch. If
                                    `chunk_size` is `None` it defaults to
                                    `WRITE_CHUNK_SIZE`.  [default: 4096]
      -t, --target TEXT             The target container name. If `target` is
                                    `None`, a default value is used instead.
      --help                        Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)
