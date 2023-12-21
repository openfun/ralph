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


def test_cli_list_command_usage():
    """Test `ralph list` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list BACKEND [OPTIONS]

      List available documents from a configured data backend.

    Options:
      --help  Show this message and exit.

    Commands:
      async_es     Asynchronous Elasticsearch data backend.
      async_mongo  Asynchronous MongoDB data backend.
      clickhouse   ClickHouse database backend.
      es           Elasticsearch data backend.
      fs           FileSystem data backend.
      ldp          OVH LDP (Log Data Platform) data backend.
      mongo        MongoDB data backend.
      s3           S3 data backend.
      swift        SWIFT data backend.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_async_es_command_usage():
    """Test the `ralph list async_es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list async_es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list async_es [OPTIONS]

      Asynchronous Elasticsearch data backend.

      List available Elasticsearch indices, data streams and aliases.

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
      -n, --new / -a, --all           Ignored.
      -D, --details / -I, --ids       Get detailed information instead of just
                                      names.
      -t, --target TEXT               The comma-separated list of data streams,
                                      indices, and aliases to limit the request.
                                      Supports wildcards (*). If target is `None`,
                                      lists all available indices, data streams and
                                      aliases. Equivalent to (`target` = "*").
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_async_mongo_command_usage():
    """Test the `ralph list async_mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list async_mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list async_mongo [OPTIONS]

      Asynchronous MongoDB data backend.

      List collections in the target database.

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
      -n, --new / -a, --all           Ignored.
      -D, --details / -I, --ids       Get detailed collection information instead of
                                      just IDs.
      -t, --target TEXT               The MongoDB database name to list collections
                                      from. If target is `None`, the
                                      `DEFAULT_DATABASE` is used instead.
      --help                          Show this message and exit.
    """
    output = output.replace("MONGO_TEST_CONNECTION_URI", MONGO_TEST_CONNECTION_URI)
    output = output.replace("MONGO_TEST_COLLECTION", MONGO_TEST_COLLECTION)
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_clickhouse_command_usage():
    """Test the `ralph list clickhouse` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list clickhouse --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list clickhouse [OPTIONS]

      ClickHouse database backend.

      List tables for a given database.

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
      -n, --new / -a, --all           Ignored.
      -D, --details / -I, --ids       Get detailed table information instead of just
                                      table names.
      -t, --target TEXT               The database name to list tables from.
      --help                          Show this message and exit.
    """
    output = output.replace("CLICKHOUSE_TEST_HOST", CLICKHOUSE_TEST_HOST)
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_es_command_usage():
    """Test the `ralph list es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list es [OPTIONS]

      Elasticsearch data backend.

      List available Elasticsearch indices, data streams and aliases.

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
      -n, --new / -a, --all           Ignored.
      -D, --details / -I, --ids       Get detailed information instead of just
                                      names.
      -t, --target TEXT               The comma-separated list of data streams,
                                      indices, and aliases to limit the request.
                                      Supports wildcards (*). If target is `None`,
                                      lists all available indices, data streams and
                                      aliases. Equivalent to (`target` = "*").
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_fs_command_usage():
    """Test the `ralph list fs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list fs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list fs [OPTIONS]

      FileSystem data backend.

      List files and directories in the target directory.

    Options:
      --default-directory-path PATH  The default target directory path where to
                                     perform list, read and write operations.
                                     [default: .]
      --default-query-string TEXT    The default query string to match files for the
                                     read operation.  [default: *]
      --locale-encoding TEXT         The encoding used for writing dictionaries to
                                     files.  [default: utf8]
      -n, --new / -a, --all          Given the history, list only not already read
                                     files.
      -D, --details / -I, --ids      Get detailed file information instead of just
                                     file paths.
      -t, --target TEXT              The directory path where to list the files and
                                     directories. If target is `None`, the
                                     `default_directory` is used instead. If target
                                     is a relative path, it is considered to be
                                     relative to the     `default_directory_path`.
      --help                         Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_ldp_command_usage():
    """Test the `ralph list ldp` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list ldp --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list ldp [OPTIONS]

      OVH LDP (Log Data Platform) data backend.

      List archives for a given target stream_id.

    Options:
      --application-key TEXT     The OVH API application key (AK).
      --application-secret TEXT  The OVH API application secret (AS).
      --consumer-key TEXT        The OVH API consumer key (CK).
      --default-stream-id TEXT   The default stream identifier to query.
      --endpoint TEXT            The OVH API endpoint.  [default: ovh-eu]
      --locale-encoding TEXT     [default: utf8]
      --request-timeout TEXT     HTTP request timeout in seconds.
      --service-name TEXT        The default LDP account name.
      -n, --new / -a, --all      Given the history, list only not already read
                                 archives.
      -D, --details / -I, --ids  Get detailed archive information in addition to
                                 archive IDs.
      -t, --target TEXT          The target stream_id where to list the archives. If
                                 target is `None`, the `DEFAULT_STREAM_ID` is used
                                 instead.
      --help                     Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_mongo_command_usage():
    """Test the `ralph list mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list mongo [OPTIONS]

      MongoDB data backend.

      List collections in the `target` database.

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
      -n, --new / -a, --all           Ignored.
      -D, --details / -I, --ids       Get detailed collection information instead of
                                      just IDs.
      -t, --target TEXT               The MongoDB database name to list collections
                                      from. If target is `None`, the
                                      `DEFAULT_DATABASE` is used instead.
      --help                          Show this message and exit.
    """
    output = output.replace("MONGO_TEST_CONNECTION_URI", MONGO_TEST_CONNECTION_URI)
    output = output.replace("MONGO_TEST_COLLECTION", MONGO_TEST_COLLECTION)
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_s3_command_usage():
    """Test the `ralph list s3` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list s3 --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list s3 [OPTIONS]

      S3 data backend.

      List objects for the target bucket.

    Options:
      --access-key-id TEXT        The access key id for the S3 account.
      --default-bucket-name TEXT  The default bucket name targeted.
      --default-region TEXT       The default region used in instantiating the
                                  client.
      --endpoint-url TEXT         The endpoint URL of the S3.
      --locale-encoding TEXT      The encoding used for writing dictionaries to
                                  objects.  [default: utf8]
      --secret-access-key TEXT    The secret key for the S3 account.
      --session-token TEXT        The session token for the S3 account.
      -n, --new / -a, --all       Given the history, list only unread files.
      -D, --details / -I, --ids   Get detailed object information instead of just
                                  object name.
      -t, --target TEXT           The target bucket to list from. If target is
                                  `None`, the `default_bucket_name` is used instead.
      --help                      Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_list_swift_command_usage():
    """Test the `ralph list swift` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "list swift --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph list swift [OPTIONS]

      SWIFT data backend.

      List files for the target container.

    Options:
      --auth-url TEXT              The authentication URL.  [default:
                                   https://auth.cloud.ovh.net/]
      --default-container TEXT     The default target container.
      --identity-api-version TEXT  The keystone API version to authenticate to.
                                   [default: 3]
      --locale-encoding TEXT       The encoding used for reading/writing documents.
                                   [default: utf8]
      --object-storage-url TEXT    The default storage URL.
      --password TEXT              The password of the openstack swift user.
      --project-domain-name TEXT   The project domain name.  [default: Default]
      --region-name TEXT           The region where the container is.
      --tenant-id TEXT             The identifier of the tenant of the container.
      --tenant-name TEXT           The name of the tenant of the container.
      --username TEXT              The name of the openstack swift user.
      --user-domain-name TEXT      The user domain name.  [default: Default]
      -n, --new / -a, --all        Given the history, list only not already read
                                   objects.
      -D, --details / -I, --ids    Get detailed object information instead of just
                                   names.
      -t, --target TEXT            The target container to list from. If `target` is
                                   `None`, the `default_container` will be used.
      --help                       Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)
