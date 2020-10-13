"""Tests for Ralph cli"""

import json
import sys
from pathlib import Path

from click.testing import CliRunner

from ralph.backends.storage.ldp import LDPStorage
from ralph.cli import cli


def test_help_option():
    """Test ralph --help command"""

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert (
        "-v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO or DEBUG"
        in result.output
    )


def test_extract_command_usage():
    """Test ralph extract command usage"""

    runner = CliRunner()
    result = runner.invoke(cli, ["extract", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -p, --parser [gelf]      Container format parser used to extract events\n"
        "                           [required]\n\n"
        "  -c, --chunksize INTEGER  Parse events by chunks of size #\n"
    ) in result.output

    result = runner.invoke(cli, ["extract"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-p' / '--parser'.  Choose from:\n\tgelf."
    ) in result.output


def test_extract_command_with_gelf_parser(gelf_logger):
    """Test the extract command using the GELF parser"""

    gelf_logger.info('{"username": "foo"}')

    runner = CliRunner()
    with Path(gelf_logger.handlers[0].stream.name).open() as log_file:
        gelf_content = log_file.read()
        result = runner.invoke(cli, ["extract", "-p", "gelf"], input=gelf_content)
        assert '{"username": "foo"}' in result.output


def test_fetch_command_usage():
    """Test ralph fetch command usage"""

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  ldp storage backend: \n"
        "    --ldp-stream-id TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "  -b, --backend [ldp]             Storage backend  [required]\n"
    ) in result.output

    result = runner.invoke(cli, ["fetch"])
    assert result.exit_code > 0
    assert "Error: Missing argument 'ARCHIVE'." in result.output


def test_fetch_command_with_ldp_backend(monkeypatch):
    """Test the fetch command using the LDP backend"""

    archive_content = {"foo": "bar"}

    def mock_read(this, name):
        """Always return the same archive"""
        # pylint: disable=unused-argument

        sys.stdout.buffer.write(bytes(json.dumps(archive_content), encoding="utf-8"))

    monkeypatch.setattr(LDPStorage, "read", mock_read)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "fetch",
            "-b",
            "ldp",
            "--ldp-endpoint",
            "ovh-eu",
            "a547d9b3-6f2f-4913-a872-cf4efe699a66",
        ],
    )

    assert result.exit_code == 0
    assert '{"foo": "bar"}' in result.output


def test_list_command_usage():
    """Test ralph list command usage"""

    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  ldp storage backend: \n"
        "    --ldp-stream-id TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "  -b, --backend [ldp]             Storage backend  [required]\n"
        "  -n, --new / -a, --all           List not fetched (or all) archives\n"
        "  -D, --details / -I, --ids       Get archives detailled output (JSON)\n"
    ) in result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'.  Choose from:\n\tldp."
        in result.output
    )


def test_list_command_with_ldp_backend(monkeypatch):
    """Test the list command using the LDP backend"""

    archive_list = [
        "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
        "997db3eb-b9ca-485d-810f-b530a6cef7c6",
    ]
    archive_list_details = [
        {
            "archiveId": "5d5c4c93-04a4-42c5-9860-f51fa4044aa1",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-16.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc507acf091ada39dbdc9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
        {
            "archiveId": "997db3eb-b9ca-485d-810f-b530a6cef7c6",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-17.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc507acf091ada39dbdc9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
    ]

    def mock_list(this, details=False, new=False):
        """Mock LDP backend list method"""
        # pylint: disable=unused-argument

        response = archive_list
        if details:
            response = archive_list_details
        if new:
            response = response[1:]
        return response

    monkeypatch.setattr(LDPStorage, "list", mock_list)

    runner = CliRunner()

    # List archives with default options
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu"])
    assert result.exit_code == 0
    assert "\n".join(archive_list) in result.output

    # List archives with detailled output
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu", "-D"])
    assert result.exit_code == 0
    assert (
        "\n".join(json.dumps(detail) for detail in archive_list_details)
        in result.output
    )

    # List new archives only
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu", "-n"])
    assert result.exit_code == 0
    assert "997db3eb-b9ca-485d-810f-b530a6cef7c6" in result.output
    assert "5d5c4c93-04a4-42c5-9860-f51fa4044aa1" not in result.output

    # Edge case: stream contains no archive
    monkeypatch.setattr(LDPStorage, "list", lambda this, details, new: ())
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu"])
    assert result.exit_code == 0
    assert "Configured ldp backend contains no archive" in result.output
