"""Tests for Ralph cli usage strings."""
from click.testing import CliRunner

from ralph.cli import cli


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
