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
    assert (
        "Options:\n"
        "  -u, --username TEXT  The user for which we generate credentials.  "
        "[required]\n"
        "  -p, --password TEXT  The password to encrypt for this user. Will be "
        "prompted\n"
        "                       if missing.  [required]\n"
        "  -s, --scope TEXT     The user scope(s). This option can be provided "
        "multiple\n"
        "                       times.  [required]\n"
        "  -w, --write          Write new credentials to the LRS authentication file.\n"
    ) in result.output

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
        "    -p, --platform-url TEXT       The `actor.account.homePage` to use in the\n"
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
    """Tests ralph fetch command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["fetch", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -b, --backend [es|mongo|clickhouse|ldp|fs|swift|s3|ws]\n"
        "                                  Backend  [required]\n"
        "  ws backend: \n"
        "    --ws-uri TEXT\n"
        "  s3 backend: \n"
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
        '  -q, --query \'{"KEY": "VALUE", "KEY": "VALUE"}\'\n'
        "                                  Query object as a JSON string (database\n"
        "                                  backends ONLY)\n"
    ) in result.output
    logging.warning(result.output)
    result = runner.invoke(cli, ["fetch"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. "
        "Choose from:\n\tes,\n\tmongo,\n\tclickhouse,\n\tldp,\n\tfs,\n\tswift,\n\ts3,"
        "\n\tws\n"
    ) in result.output


def test_cli_list_command_usage():
    """Tests ralph list command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -b, --backend [ldp|fs|swift|s3]\n"
        "                                  Backend  [required]\n"
        "  s3 backend: \n"
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


def test_cli_runserver_command_usage():
    """Tests ralph runserver command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["runserver", "--help"])

    expected_output = (
        "Options:\n"
        "  -b, --backend [es|mongo|clickhouse]\n"
        "                                  Backend  [required]\n"
        "  clickhouse backend: \n"
        "    --clickhouse-client-options KEY=VALUE,KEY=VALUE\n"
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
