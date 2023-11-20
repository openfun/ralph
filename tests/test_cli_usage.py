"""Tests for Ralph cli usage strings."""
import logging

from click.testing import CliRunner

from ralph.cli import cli

test_logger = logging.getLogger("ralph")


def test_cli_auth_command_usage():
    """Test ralph auth command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "--help"])

    assert result.exit_code == 0
    assert all(
        text in result.output
        for text in [
            "Options:",
            "-u, --username TEXT",
            "-p, --password TEXT",
            "-s, --scope TEXT",
            "-M, --agent-ifi-mbox TEXT",
            "-S, --agent-ifi-mbox-sha1sum TEXT",
            "-O, --agent-ifi-openid TEXT",
            "-A, --agent-ifi-account TEXT",
            "-N, --agent-name TEXT",
            "-w, --write-to-disk",
        ]
    )

    result = runner.invoke(cli, ["auth"])
    assert result.exit_code > 0
    assert "Error: Missing option '-u' / '--username'." in result.output


def test_cli_extract_command_usage():
    """Test ralph extract command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["extract", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -p, --parser [gelf|es]  Container format parser used to extract events\n"
        "                          [required]\n"
    ) in result.output

    result = runner.invoke(cli, ["extract"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-p' / '--parser'. Choose from:\n\tgelf,\n\tes\n"
    ) in result.output


def test_cli_validate_command_usage():
    """Test ralph validate command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -f, --format [edx|xapi]  Input events format to validate  [required]\n"
        "  -I, --ignore-errors      Continue validating regardless of raised errors\n"
        "  -F, --fail-on-unknown    Stop validating at first unknown event\n"
    ) in result.output

    result = runner.invoke(cli, ["validate"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-f' / '--format'. Choose from:\n\tedx,\n\txapi\n"
    ) in result.output


def test_cli_convert_command_usage():
    """Test ralph convert command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  From edX to xAPI converter options: \n"
        "    -u, --uuid-namespace TEXT     The UUID namespace to use for the `ID` "
        "field\n"
        "                                  generation\n"
        "    -p, --platform-url TEXT       The `actor.account.homePage` to use in"
        " the\n"
        "                                  xAPI statements  [required]\n"
        "  -f, --from [edx]                Input events format to convert  [required]\n"
        "  -t, --to [xapi]                 Output events format  [required]\n"
        "  -I, --ignore-errors             Continue writing regardless of raised "
        "errors\n"
        "  -F, --fail-on-unknown           Stop converting at first unknown event\n"
    ) in result.output

    result = runner.invoke(cli, ["convert"])
    assert result.exit_code > 0
    assert "Error: Missing option '-p' / '--platform-url'" in result.output


def test_cli_read_command_usage():
    """Test ralph read command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["read", "--help"])

    assert result.exit_code == 0
    assert (
        "Usage: ralph read [OPTIONS] [ARCHIVE]\n\n"
        "  Read an archive or records from a configured backend.\n\n"
        "Options:\n"
        "  -b, --backend "
        "[async_es|async_lrs|async_mongo|clickhouse|es|fs|ldp|lrs|mongo|s3|swift|ws]\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_lrs backend: \n"
        "    --async-lrs-base-url TEXT\n"
        "    --async-lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --async-lrs-locale-encoding TEXT\n"
        "    --async-lrs-password TEXT\n"
        "    --async-lrs-read-chunk-size INTEGER\n"
        "    --async-lrs-statements-endpoint TEXT\n"
        "    --async-lrs-status-endpoint TEXT\n"
        "    --async-lrs-username TEXT\n"
        "    --async-lrs-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri MONGODSN\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-host TEXT\n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-read-chunk-size INTEGER\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  ldp backend: \n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-default-stream-id TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "    --ldp-locale-encoding TEXT\n"
        "    --ldp-read-chunk-size INTEGER\n"
        "    --ldp-request-timeout TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-write-chunk-size INTEGER\n"
        "  lrs backend: \n"
        "    --lrs-base-url TEXT\n"
        "    --lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --lrs-locale-encoding TEXT\n"
        "    --lrs-password TEXT\n"
        "    --lrs-read-chunk-size INTEGER\n"
        "    --lrs-statements-endpoint TEXT\n"
        "    --lrs-status-endpoint TEXT\n"
        "    --lrs-username TEXT\n"
        "    --lrs-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri MONGODSN\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  s3 backend: \n"
        "    --s3-access-key-id TEXT\n"
        "    --s3-default-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-locale-encoding TEXT\n"
        "    --s3-read-chunk-size INTEGER\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-write-chunk-size INTEGER\n"
        "  swift backend: \n"
        "    --swift-auth-url TEXT\n"
        "    --swift-default-container TEXT\n"
        "    --swift-identity-api-version TEXT\n"
        "    --swift-locale-encoding TEXT\n"
        "    --swift-object-storage-url TEXT\n"
        "    --swift-password TEXT\n"
        "    --swift-project-domain-name TEXT\n"
        "    --swift-read-chunk-size INTEGER\n"
        "    --swift-region-name TEXT\n"
        "    --swift-tenant-id TEXT\n"
        "    --swift-tenant-name TEXT\n"
        "    --swift-username TEXT\n"
        "    --swift-user-domain-name TEXT\n"
        "    --swift-write-chunk-size INTEGER\n"
        "  ws backend: \n"
        "    --ws-uri TEXT\n"
        "  -s, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -t, --target TEXT               Endpoint from which to read events (e.g.\n"
        "                                  `/statements`)\n"
        '  -q, --query \'{"KEY": "VALUE", "KEY": "VALUE"}\'\n'
        "                                  Query object as a JSON string (database and"
        "\n"
        "                                  HTTP backends ONLY)\n"
        "  -i, --ignore_errors BOOLEAN     Ignore errors during the encoding operation."
        "\n"
        "                                  [default: False]\n"
        "  --help                          Show this message and exit.\n"
    ) == result.output
    logging.warning(result.output)
    result = runner.invoke(cli, ["read"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. "
        "Choose from:\n\tasync_es,\n\tasync_lrs,\n\tasync_mongo,\n\tclickhouse,\n\tes,"
        "\n\tfs,\n\tldp,\n\tlrs,\n\tmongo,\n\ts3,\n\tswift,\n\tws\n"
    ) in result.output


def test_cli_list_command_usage():
    """Test ralph list command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Usage: ralph list [OPTIONS]\n\n"
        "  List available documents from a configured data backend.\n\n"
        "Options:\n"
        "  -b, --backend [async_es|async_mongo|clickhouse|es|fs|ldp|mongo|s3|swift]\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri MONGODSN\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-host TEXT\n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-read-chunk-size INTEGER\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  ldp backend: \n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-default-stream-id TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "    --ldp-locale-encoding TEXT\n"
        "    --ldp-read-chunk-size INTEGER\n"
        "    --ldp-request-timeout TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri MONGODSN\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  s3 backend: \n"
        "    --s3-access-key-id TEXT\n"
        "    --s3-default-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-locale-encoding TEXT\n"
        "    --s3-read-chunk-size INTEGER\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-write-chunk-size INTEGER\n"
        "  swift backend: \n"
        "    --swift-auth-url TEXT\n"
        "    --swift-default-container TEXT\n"
        "    --swift-identity-api-version TEXT\n"
        "    --swift-locale-encoding TEXT\n"
        "    --swift-object-storage-url TEXT\n"
        "    --swift-password TEXT\n"
        "    --swift-project-domain-name TEXT\n"
        "    --swift-read-chunk-size INTEGER\n"
        "    --swift-region-name TEXT\n"
        "    --swift-tenant-id TEXT\n"
        "    --swift-tenant-name TEXT\n"
        "    --swift-username TEXT\n"
        "    --swift-user-domain-name TEXT\n"
        "    --swift-write-chunk-size INTEGER\n"
        "  -t, --target TEXT               Container to list events from\n"
        "  -n, --new / -a, --all           List not fetched (or all) documents\n"
        "  -D, --details / -I, --ids       Get documents detailed output (JSON)\n"
        "  --help                          Show this message and exit.\n"
    ) == result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\t"
        "async_mongo,\n\tclickhouse,\n\tes,\n\tfs,\n\tldp,\n\tmongo,\n\ts3,"
        "\n\tswift\n"
    ) in result.output


def test_cli_write_command_usage():
    """Test ralph write command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["write", "--help"])

    assert result.exit_code == 0

    expected_output = (
        "Usage: ralph write [OPTIONS]\n\n"
        "  Write an archive to a configured backend.\n\n"
        "Options:\n"
        "  -b, --backend "
        "[async_es|async_lrs|async_mongo|clickhouse|es|fs|lrs|mongo|s3|swift]"
        "\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_lrs backend: \n"
        "    --async-lrs-base-url TEXT\n"
        "    --async-lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --async-lrs-locale-encoding TEXT\n"
        "    --async-lrs-password TEXT\n"
        "    --async-lrs-read-chunk-size INTEGER\n"
        "    --async-lrs-statements-endpoint TEXT\n"
        "    --async-lrs-status-endpoint TEXT\n"
        "    --async-lrs-username TEXT\n"
        "    --async-lrs-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri MONGODSN\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-host TEXT\n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-read-chunk-size INTEGER\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  lrs backend: \n"
        "    --lrs-base-url TEXT\n"
        "    --lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --lrs-locale-encoding TEXT\n"
        "    --lrs-password TEXT\n"
        "    --lrs-read-chunk-size INTEGER\n"
        "    --lrs-statements-endpoint TEXT\n"
        "    --lrs-status-endpoint TEXT\n"
        "    --lrs-username TEXT\n"
        "    --lrs-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri MONGODSN\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  s3 backend: \n"
        "    --s3-access-key-id TEXT\n"
        "    --s3-default-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-locale-encoding TEXT\n"
        "    --s3-read-chunk-size INTEGER\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-write-chunk-size INTEGER\n"
        "  swift backend: \n"
        "    --swift-auth-url TEXT\n"
        "    --swift-default-container TEXT\n"
        "    --swift-identity-api-version TEXT\n"
        "    --swift-locale-encoding TEXT\n"
        "    --swift-object-storage-url TEXT\n"
        "    --swift-password TEXT\n"
        "    --swift-project-domain-name TEXT\n"
        "    --swift-read-chunk-size INTEGER\n"
        "    --swift-region-name TEXT\n"
        "    --swift-tenant-id TEXT\n"
        "    --swift-tenant-name TEXT\n"
        "    --swift-username TEXT\n"
        "    --swift-user-domain-name TEXT\n"
        "    --swift-write-chunk-size INTEGER\n"
        "  -t, --target TEXT               The target container to write into\n"
        "  -s, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -I, --ignore-errors             Continue writing regardless of raised errors"
        "\n"
        "  -o, --operation-type OP_TYPE    Either index, create, delete, update or "
        "append\n"
        "  -c, --concurrency INTEGER       Number of chunks to write concurrently. ("
        "async\n"
        "                                  backends only)\n"
        "  --help                          Show this message and exit.\n"
    )
    assert expected_output == result.output

    result = runner.invoke(cli, ["write"])
    assert result.exit_code > 0
    assert (
        "Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\tasync_lrs,\n\t"
        "async_mongo,\n\tclickhouse,\n\tes,\n\tfs,\n\tlrs,\n\tmongo,\n\ts3,\n\tswift\n"
    ) in result.output


def test_cli_runserver_command_usage():
    """Test ralph runserver command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["runserver", "--help"])

    expected_output = (
        "Usage: ralph runserver [OPTIONS]\n\n"
        "  Run the API server for the development environment.\n\n"
        "  Starts uvicorn programmatically for convenience and documentation.\n\n"
        "Options:\n"
        "  -b, --backend [async_es|async_mongo|clickhouse|es|fs|mongo]\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri MONGODSN\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-host TEXT\n"
        "    --clickhouse-ids-chunk-size INTEGER\n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-read-chunk-size INTEGER\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-lrs-file TEXT\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri MONGODSN\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  -h, --host TEXT                 LRS server host name\n"
        "  -p, --port INTEGER              LRS server port\n"
        "  --help                          Show this message and exit.\n"
    )
    assert result.exit_code == 0
    assert expected_output in result.output

    result = runner.invoke(cli, ["runserver"])
    assert result.exit_code > 0
    assert (
        "Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\tasync_mongo,\n"
        "\tclickhouse,\n\tes,\n\tfs,\n\tmongo\n"
    ) in result.output
