"""Tests for Ralph cli read usage strings."""

import re

from click.testing import CliRunner

from ralph.cli import cli

from tests.fixtures.backends import ES_TEST_HOSTS


def test_cli_runserver_command_usage():
    """Test `ralph runserver` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "runserver --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph runserver BACKEND [OPTIONS]

      Run the API server for the development environment.

      Start uvicorn programmatically for convenience and documentation.

    Options:
      --help  Show this message and exit.

    Commands:
      async_es     Asynchronous Elasticsearch LRS backend implementation.
      async_mongo  Async MongoDB LRS backend implementation.
      clickhouse   ClickHouse LRS backend implementation.
      es           Elasticsearch LRS backend implementation.
      fs           FileSystem LRS Backend.
      mongo        MongoDB LRS backend.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_runserver_async_es_command_usage():
    """Test the `ralph runserver async_es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "runserver async_es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph runserver async_es [OPTIONS]

      Asynchronous Elasticsearch LRS backend implementation.

      Run the API server for the development environment.

    Options:
      --allow-yellow-status / --no-allow-yellow-status
                                      [default: no-allow-yellow-status]
      --client-options KEY=VALUE,KEY=VALUE
                                      [default: ca_certs=None verify_certs=None]
      --default-index TEXT            [default: statements]
      --hosts VALUE1,VALUE2,VALUE3    [default: ES_TEST_HOSTS]
      --locale-encoding TEXT          [default: utf8]
      --point-in-time-keep-alive TEXT
                                      [default: 1m]
      --refresh-after-write TEXT
      -h, --host TEXT
      -p, --port INTEGER
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_runserver_async_mongo_command_usage():
    """Test the `ralph runserver async_mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "runserver async_mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph runserver async_mongo [OPTIONS]

      Async MongoDB LRS backend implementation.

      Run the API server for the development environment.

    Options:
      --client-options KEY=VALUE,KEY=VALUE
                                      [default: document_class=None tz_aware=None]
      --connection-uri TEXT           [default: mongodb://localhost:27017/]
      --default-collection TEXT       [default: marsha]
      --default-database TEXT         [default: statements]
      --locale-encoding TEXT          [default: utf8]
      -h, --host TEXT
      -p, --port INTEGER
      --help                          Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_runserver_clickhouse_command_usage():
    """Test the `ralph runserver clickhouse` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "runserver clickhouse --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph runserver clickhouse [OPTIONS]

      ClickHouse LRS backend implementation.

      Run the API server for the development environment.

    Options:
      --client-options KEY=VALUE,KEY=VALUE
                                      [default:
                                      date_time_input_format='best_effort']
      --database TEXT                 [default: xapi]
      --event-table-name TEXT         [default: xapi_events_all]
      --host TEXT                     [default: localhost]
      --ids-chunk-size INTEGER        The chunk size for querying by ids.  [default:
                                      10000]
      --locale-encoding TEXT          [default: utf8]
      --password TEXT
      --port INTEGER                  [default: 8123]
      --username TEXT
      -h, --host TEXT
      -p, --port INTEGER
      --help                          Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_runserver_es_command_usage():
    """Test the `ralph runserver es` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "runserver es --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph runserver es [OPTIONS]

      Elasticsearch LRS backend implementation.

      Run the API server for the development environment.

    Options:
      --allow-yellow-status / --no-allow-yellow-status
                                      [default: no-allow-yellow-status]
      --client-options KEY=VALUE,KEY=VALUE
                                      [default: ca_certs=None verify_certs=None]
      --default-index TEXT            [default: statements]
      --hosts VALUE1,VALUE2,VALUE3    [default: ES_TEST_HOSTS]
      --locale-encoding TEXT          [default: utf8]
      --point-in-time-keep-alive TEXT
                                      [default: 1m]
      --refresh-after-write TEXT
      -h, --host TEXT
      -p, --port INTEGER
      --help                          Show this message and exit.
    """
    output = output.replace("ES_TEST_HOSTS", "".join(ES_TEST_HOSTS))
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_runserver_fs_command_usage():
    """Test the `ralph runserver fs` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "runserver fs --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph runserver fs [OPTIONS]

      FileSystem LRS Backend.

      Run the API server for the development environment.

    Options:
      --default-directory-path PATH  [default: .]
      --default-lrs-file TEXT        The default LRS filename to store statements.
                                     [default: fs_lrs.jsonl]
      --default-query-string TEXT    [default: *]
      --locale-encoding TEXT         [default: utf8]
      -h, --host TEXT
      -p, --port INTEGER
      --help                         Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)


def test_cli_runserver_mongo_command_usage():
    """Test the `ralph runserver mongo` command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, "runserver mongo --help".split())

    assert result.exit_code == 0
    output = """Usage: ralph runserver mongo [OPTIONS]

      MongoDB LRS backend.

      Run the API server for the development environment.

    Options:
      --client-options KEY=VALUE,KEY=VALUE
                                      [default: document_class=None tz_aware=None]
      --connection-uri TEXT           [default: mongodb://localhost:27017/]
      --default-collection TEXT       [default: marsha]
      --default-database TEXT         [default: statements]
      --locale-encoding TEXT          [default: utf8]
      -h, --host TEXT
      -p, --port INTEGER
      --help                          Show this message and exit.
    """
    assert result.output == re.sub(re.compile(r"^ {4}", re.MULTILINE), "", output)
