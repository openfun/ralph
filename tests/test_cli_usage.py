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
        "  -b, --backend [async_es|async_mongo|clickhouse|es|fs|ldp|mongo|swift|s3|lrs|"
        "ws]\n"
        "                                  Backend  [required]\n"
        "  ws backend: \n"
        "    --ws-uri TEXT\n"
        "  lrs backend: \n"
        "    --lrs-statements-endpoint TEXT\n"
        "    --lrs-status-endpoint TEXT\n"
        "    --lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --lrs-password TEXT\n"
        "    --lrs-username TEXT\n"
        "    --lrs-base-url TEXT\n"
        "  s3 backend: \n"
        "    --s3-locale-encoding TEXT\n"
        "    --s3-default-chunk-size INTEGER\n"
        "    --s3-default-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-access-key-id TEXT\n"
        "  swift backend: \n"
        "    --swift-locale-encoding TEXT\n"
        "    --swift-default-container TEXT\n"
        "    --swift-user-domain-name TEXT\n"
        "    --swift-object-storage-url TEXT\n"
        "    --swift-region-name TEXT\n"
        "    --swift-project-domain-name TEXT\n"
        "    --swift-tenant-name TEXT\n"
        "    --swift-tenant-id TEXT\n"
        "    --swift-identity-api-version TEXT\n"
        "    --swift-password TEXT\n"
        "    --swift-username TEXT\n"
        "    --swift-auth-url TEXT\n"
        "  mongo backend: \n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-default-chunk-size INTEGER\n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-connection-uri TEXT\n"
        "  ldp backend: \n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-request-timeout TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "    --ldp-default-stream-id TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "  fs backend: \n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-default-index TEXT\n"
        "    --es-default-chunk-size INTEGER\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "  clickhouse backend: \n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-default-chunk-size INTEGER\n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-host TEXT\n"
        "  async_mongo backend: \n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-default-chunk-size INTEGER\n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-connection-uri TEXT\n"
        "  async_es backend: \n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-default-chunk-size INTEGER\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "  -c, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -t, --target TEXT               Endpoint from which to read events (e.g.\n"
        "                                  `/statements`)\n"
        '  -q, --query \'{"KEY": "VALUE", "KEY": "VALUE"}\'\n'
        "                                  Query object as a JSON string (database and"
        "\n"
        "                                  HTTP backends ONLY)\n"
        "  -r, --raw-output                Yield bytes instead of dictionaries.\n"
        "                                  [default: True]\n"
        "  -i, --ignore_errors BOOLEAN     Ignore errors during the encoding operation."
        "\n"
        "                                  [default: False]\n"
        "  --help                          Show this message and exit."
    ) in result.output
    logging.warning(result.output)
    result = runner.invoke(cli, ["read"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. "
        "Choose from:\n\tasync_es,\n\tasync_mongo,\n\tclickhouse,\n\tes,\n\tfs,\n\tldp,"
        "\n\tmongo,\n\tswift,\n\ts3,\n\tlrs,\n\tws\n"
    ) in result.output


def test_cli_list_command_usage():
    """Test ralph list command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Usage: ralph list [OPTIONS]\n\n"
        "  List available archives from a configured storage backend.\n\n"
        "Options:\n"
        "  -b, --backend [async_es|async_mongo|clickhouse|es|fs|ldp|mongo|swift|s3]\n"
        "                                  Backend  [required]\n"
        "  s3 backend: \n"
        "    --s3-locale-encoding TEXT\n"
        "    --s3-default-chunk-size INTEGER\n"
        "    --s3-default-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-access-key-id TEXT\n"
        "  swift backend: \n"
        "    --swift-locale-encoding TEXT\n"
        "    --swift-default-container TEXT\n"
        "    --swift-user-domain-name TEXT\n"
        "    --swift-object-storage-url TEXT\n"
        "    --swift-region-name TEXT\n"
        "    --swift-project-domain-name TEXT\n"
        "    --swift-tenant-name TEXT\n"
        "    --swift-tenant-id TEXT\n"
        "    --swift-identity-api-version TEXT\n"
        "    --swift-password TEXT\n"
        "    --swift-username TEXT\n"
        "    --swift-auth-url TEXT\n"
        "  mongo backend: \n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-default-chunk-size INTEGER\n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-connection-uri TEXT\n"
        "  ldp backend: \n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-request-timeout TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "    --ldp-default-stream-id TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "  fs backend: \n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-default-index TEXT\n"
        "    --es-default-chunk-size INTEGER\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "  clickhouse backend: \n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-default-chunk-size INTEGER\n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-host TEXT\n"
        "  async_mongo backend: \n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-default-chunk-size INTEGER\n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-connection-uri TEXT\n"
        "  async_es backend: \n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-default-chunk-size INTEGER\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "  -t, --target TEXT               Container to list events from\n"
        "  -n, --new / -a, --all           List not fetched (or all) archives\n"
        "  -D, --details / -I, --ids       Get archives detailed output (JSON)\n"
        "  --help                          Show this message and exit.\n"
    ) in result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\t"
        "async_mongo,\n\tclickhouse,\n\tes,\n\tfs,\n\tldp,\n\tmongo,\n\tswift,"
        "\n\ts3\n"
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
        "  -b, --backend [async_es|async_mongo|clickhouse|es|fs|ldp|mongo|swift|s3|lrs]"
        "\n"
        "                                  Backend  [required]\n"
        "  lrs backend: \n"
        "    --lrs-statements-endpoint TEXT\n"
        "    --lrs-status-endpoint TEXT\n"
        "    --lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --lrs-password TEXT\n"
        "    --lrs-username TEXT\n"
        "    --lrs-base-url TEXT\n"
        "  s3 backend: \n"
        "    --s3-locale-encoding TEXT\n"
        "    --s3-default-chunk-size INTEGER\n"
        "    --s3-default-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-access-key-id TEXT\n"
        "  swift backend: \n"
        "    --swift-locale-encoding TEXT\n"
        "    --swift-default-container TEXT\n"
        "    --swift-user-domain-name TEXT\n"
        "    --swift-object-storage-url TEXT\n"
        "    --swift-region-name TEXT\n"
        "    --swift-project-domain-name TEXT\n"
        "    --swift-tenant-name TEXT\n"
        "    --swift-tenant-id TEXT\n"
        "    --swift-identity-api-version TEXT\n"
        "    --swift-password TEXT\n"
        "    --swift-username TEXT\n"
        "    --swift-auth-url TEXT\n"
        "  mongo backend: \n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-default-chunk-size INTEGER\n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-connection-uri TEXT\n"
        "  ldp backend: \n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-request-timeout TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "    --ldp-default-stream-id TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "  fs backend: \n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-default-index TEXT\n"
        "    --es-default-chunk-size INTEGER\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "  clickhouse backend: \n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-default-chunk-size INTEGER\n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-host TEXT\n"
        "  async_mongo backend: \n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-default-chunk-size INTEGER\n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-connection-uri TEXT\n"
        "  async_es backend: \n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-default-chunk-size INTEGER\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "  -c, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -f, --force                     Overwrite existing archives or records\n"
        "  -I, --ignore-errors             Continue writing regardless of raised errors"
        "\n"
        "  -s, --simultaneous              With HTTP backend, POST all chunks\n"
        "                                  simultaneously (instead of sequentially)\n"
        "  -m, --max-num-simultaneous INTEGER\n"
        "                                  The maximum number of chunks to send at once"
        ",\n"
        "                                  when using `--simultaneous`. Use `-1` to not"
        "\n"
        "                                  set a limit.\n"
        "  -t, --target TEXT               The target container to write into\n"
        "  --help                          Show this message and exit.\n"
    )
    assert expected_output in result.output

    result = runner.invoke(cli, ["write"])
    assert result.exit_code > 0
    assert (
        "Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\tasync_mongo,\n"
        "\tclickhouse,\n\tes,\n\tfs,\n\tldp,\n\tmongo,\n\tswift,\n\ts3,\n\tlrs\n"
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
        "  mongo backend: \n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-default-chunk-size INTEGER\n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-connection-uri TEXT\n"
        "  fs backend: \n"
        "    --fs-default-lrs-file TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --es-default-index TEXT\n"
        "    --es-default-chunk-size INTEGER\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "  clickhouse backend: \n"
        "    --clickhouse-ids-chunk-size INTEGER\n"
        "    --clickhouse-locale-encoding TEXT\n"
        "    --clickhouse-default-chunk-size INTEGER\n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-host TEXT\n"
        "  async_mongo backend: \n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-default-chunk-size INTEGER\n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-connection-uri TEXT\n"
        "  async_es backend: \n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-hosts VALUE1,VALUE2,VALUE3\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-default-chunk-size INTEGER\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "  -h, --host TEXT                 LRS server host name\n"
        "  -p, --port INTEGER              LRS server port\n"
        "  --help                          Show this message and exit.\n"
    )
    assert result.exit_code == 0
    assert expected_output in result.output
