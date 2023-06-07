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
            "-w, --write",
        ]
    )

    result = runner.invoke(cli, ["auth"])
    assert result.exit_code > 0
    assert "Error: Missing option '-u' / '--username'." in result.output


def test_cli_extract_command_usage():
    """Tests ralph extract command usage."""
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
    """Tests ralph validate command usage."""
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
    """Tests ralph convert command usage."""
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


def test_cli_fetch_command_usage():
    """Test ralph fetch command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["fetch", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -b, --backend [es|mongo|clickhouse|lrs|ldp|fs|swift|s3|ws]\n"
        "                                  Backend  [required]\n"
        "  ws backend: \n"
        "    --ws-uri TEXT\n"
        "  s3 backend: \n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-access-key-id TEXT\n"
        "  swift backend: \n"
        "    --swift-os-identity-api-version TEXT\n"
        "    --swift-os-auth-url TEXT\n"
        "    --swift-os-project-domain-name TEXT\n"
        "    --swift-os-user-domain-name TEXT\n"
        "    --swift-os-storage-url TEXT\n"
        "    --swift-os-region-name TEXT\n"
        "    --swift-os-password TEXT\n"
        "    --swift-os-username TEXT\n"
        "    --swift-os-tenant-name TEXT\n"
        "    --swift-os-tenant-id TEXT\n"
        "  fs backend: \n"
        "    --fs-path TEXT\n"
        "  ldp backend: \n"
        "    --ldp-stream-id TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "  lrs backend: \n"
        "    --lrs-statements-endpoint TEXT\n"
        "    --lrs-status-endpoint TEXT\n"
        "    --lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --lrs-password TEXT\n"
        "    --lrs-username TEXT\n"
        "    --lrs-base-url TEXT\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-host TEXT\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-collection TEXT\n"
        "    --mongo-database TEXT\n"
        "    --mongo-connection-uri TEXT\n"
        "  es backend: \n"
        "    --es-op-type TEXT\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-index TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "  -c, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -t, --target TEXT               Endpoint from which to fetch events (e.g.\n"
        "                                  `/statements`)\n"
        '  -q, --query \'{"KEY": "VALUE", "KEY": "VALUE"}\'\n'
        "                                  Query object as a JSON string (database "
        "and\n"
        "                                  HTTP backends ONLY)\n"
    ) in result.output
    logging.warning(result.output)
    result = runner.invoke(cli, ["fetch"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. "
        "Choose from:\n\tes,\n\tmongo,\n\tclickhouse,\n\tlrs,\n\tldp,\n\tfs,\n\tswift,"
        "\n\ts3,\n\tws\n"
    ) in result.output


def test_cli_list_command_usage():
    """Test ralph list command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -b, --backend [ldp|fs|swift|s3]\n"
        "                                  Backend  [required]\n"
        "  s3 backend: \n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-access-key-id TEXT\n"
        "  swift backend: \n"
        "    --swift-os-identity-api-version TEXT\n"
        "    --swift-os-auth-url TEXT\n"
        "    --swift-os-project-domain-name TEXT\n"
        "    --swift-os-user-domain-name TEXT\n"
        "    --swift-os-storage-url TEXT\n"
        "    --swift-os-region-name TEXT\n"
        "    --swift-os-password TEXT\n"
        "    --swift-os-username TEXT\n"
        "    --swift-os-tenant-name TEXT\n"
        "    --swift-os-tenant-id TEXT\n"
        "  fs backend: \n"
        "    --fs-path TEXT\n"
        "  ldp backend: \n"
        "    --ldp-stream-id TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "  -n, --new / -a, --all           List not fetched (or all) archives\n"
        "  -D, --details / -I, --ids       Get archives detailed output (JSON)\n"
    ) in result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. Choose from:\n\tldp,\n\tfs,\n\t"
        "swift,\n\ts3\n"
    ) in result.output


def test_cli_push_command_usage():
    """Test ralph push command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["push", "--help"])

    assert result.exit_code == 0

    expected_output = (
        "Usage: ralph push [OPTIONS] [ARCHIVE]\n"
        "\n"
        "  Push an archive to a configured backend.\n"
        "\n"
        "Options:\n"
        "  -b, --backend [es|mongo|clickhouse|ldp|fs|swift|s3|lrs]\n"
        "                                  Backend  [required]\n"
        "  lrs backend: \n"
        "    --lrs-statements-endpoint TEXT\n"
        "    --lrs-status-endpoint TEXT\n"
        "    --lrs-headers KEY=VALUE,KEY=VALUE\n"
        "    --lrs-password TEXT\n"
        "    --lrs-username TEXT\n"
        "    --lrs-base-url TEXT\n"
        "  s3 backend: \n"
        "    --s3-endpoint-url TEXT\n"
        "    --s3-bucket-name TEXT\n"
        "    --s3-default-region TEXT\n"
        "    --s3-session-token TEXT\n"
        "    --s3-secret-access-key TEXT\n"
        "    --s3-access-key-id TEXT\n"
        "  swift backend: \n"
        "    --swift-os-identity-api-version TEXT\n"
        "    --swift-os-auth-url TEXT\n"
        "    --swift-os-project-domain-name TEXT\n"
        "    --swift-os-user-domain-name TEXT\n"
        "    --swift-os-storage-url TEXT\n"
        "    --swift-os-region-name TEXT\n"
        "    --swift-os-password TEXT\n"
        "    --swift-os-username TEXT\n"
        "    --swift-os-tenant-name TEXT\n"
        "    --swift-os-tenant-id TEXT\n"
        "  fs backend: \n"
        "    --fs-path TEXT\n"
        "  ldp backend: \n"
        "    --ldp-stream-id TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-host TEXT\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-collection TEXT\n"
        "    --mongo-database TEXT\n"
        "    --mongo-connection-uri TEXT\n"
        "  es backend: \n"
        "    --es-op-type TEXT\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-index TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "  -c, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -f, --force                     Overwrite existing archives or records\n"
        "  -I, --ignore-errors             Continue writing regardless of raised "
        "errors\n"
        "  -s, --simultaneous              With HTTP backend, POST all chunks\n"
        "                                  simultaneously (instead of sequentially)\n"
        "  -m, --max-num-simultaneous INTEGER\n"
        "                                  The maximum number of chunks to send at "
        "once,\n"
        "                                  when using `--simultaneous`. Use `-1` to "
        "not\n"
        "                                  set a limit.\n"
        "  -t, --target TEXT               Endpoint in which to push events (e.g.\n"
        "                                  `statements`)\n"
        "  --help                          Show this message and exit.\n"
    )
    assert expected_output in result.output

    result = runner.invoke(cli, ["push"])
    assert result.exit_code > 0
    assert (
        "Missing option '-b' / '--backend'. Choose from:\n\tes,\n\tmongo,"
        "\n\tclickhouse,\n\tldp,\n\tfs,\n\tswift,\n\ts3,\n\tlrs\n"
    ) in result.output


def test_cli_runserver_command_usage():
    """Test ralph runserver command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["runserver", "--help"])

    expected_output = (
        "Options:\n"
        "  -b, --backend [es|mongo|clickhouse]\n"
        "                                  Backend  [required]\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
        "    --clickhouse-password TEXT\n"
        "    --clickhouse-username TEXT\n"
        "    --clickhouse-event-table-name TEXT\n"
        "    --clickhouse-database TEXT\n"
        "    --clickhouse-port INTEGER\n"
        "    --clickhouse-host TEXT\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-collection TEXT\n"
        "    --mongo-database TEXT\n"
        "    --mongo-connection-uri TEXT\n"
        "  es backend: \n"
        "    --es-op-type TEXT\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-index TEXT\n"
        "    --es-hosts VALUE1,VALUE2,VALUE3\n"
        "  -h, --host TEXT                 LRS server host name\n"
        "  -p, --port INTEGER              LRS server port\n"
    )

    assert result.exit_code == 0
    assert expected_output in result.output
