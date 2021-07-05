"""Tests for Ralph cli"""

import json
import logging
import sys
from pathlib import Path

import pytest
from click.exceptions import BadParameter
from click.testing import CliRunner
from elasticsearch.helpers import bulk, scan
from hypothesis import given, provisional, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from ralph.backends.storage.fs import FSStorage
from ralph.backends.storage.ldp import LDPStorage
from ralph.cli import CommaSeparatedKeyValueParamType, cli
from ralph.defaults import APP_DIR, FS_STORAGE_DEFAULT_PATH
from ralph.exceptions import ConfigurationException
from ralph.models.edx.navigational import UIPageClose
from ralph.models.xapi.navigation.statements import PageTerminated

from tests.fixtures.backends import ES_TEST_HOSTS, ES_TEST_INDEX

test_logger = logging.getLogger("ralph")


def test_cli_comma_separated_key_value_param_type():
    """Tests the CommaSeparatedKeyValueParamType custom parameter type."""

    param_type = CommaSeparatedKeyValueParamType()

    # Bad options
    with pytest.raises(
        BadParameter,
        match="You should provide key=value pairs separated by commas, e.g. foo=bar,bar=2",
    ):
        param_type.convert("foo=bar,baz", None, None)
    with pytest.raises(
        BadParameter,
        match="You should provide key=value pairs separated by commas, e.g. foo=bar,bar=2",
    ):
        param_type.convert("foo=bar,", None, None)

    # Simple string parsing
    assert param_type.convert("foo=bar", None, None) == {
        "foo": "bar",
    }
    assert param_type.convert("foo=bar,baz=spam", None, None) == {
        "foo": "bar",
        "baz": "spam",
    }
    assert param_type.convert("foo=bar,baz=", None, None) == {
        "foo": "bar",
        "baz": None,
    }

    # Boolean type casting
    assert param_type.convert("foo=true,bar=false", None, None) == {
        "foo": True,
        "bar": False,
    }
    assert param_type.convert("foo=True,bar=False", None, None) == {
        "foo": True,
        "bar": False,
    }

    # Integer type casting
    assert param_type.convert("foo=42,bar=1", None, None) == {
        "foo": 42,
        "bar": 1,
    }

    # Float type casting
    assert param_type.convert("foo=4.2,bar=12.3", None, None) == {
        "foo": 4.2,
        "bar": 12.3,
    }

    # Mixed types casting
    assert param_type.convert("foo=lol,bar=12.3,baz=1,spam=True", None, None) == {
        "foo": "lol",
        "bar": 12.3,
        "baz": 1,
        "spam": True,
    }


def test_cli_help_option():
    """Tests ralph --help command."""

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert (
        "-v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO (default) or DEBUG"
        in result.output
    )


def test_cli_extract_command_usage():
    """Tests ralph extract command usage."""

    runner = CliRunner()
    result = runner.invoke(cli, ["extract", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -p, --parser [gelf]  Container format parser used to extract events\n"
        "                       [required]\n"
    ) in result.output

    result = runner.invoke(cli, ["extract"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-p' / '--parser'. Choose from:\n\tgelf\n"
    ) in result.output


def test_cli_extract_command_with_gelf_parser(gelf_logger):
    """Tests the extract command using the GELF parser."""

    gelf_logger.info('{"username": "foo"}')

    runner = CliRunner()
    with Path(gelf_logger.handlers[0].stream.name).open() as log_file:
        gelf_content = log_file.read()
        result = runner.invoke(cli, ["extract", "-p", "gelf"], input=gelf_content)
        assert '{"username": "foo"}' in result.output


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


@settings(max_examples=1)
@given(
    st.builds(UIPageClose, referer=provisional.urls(), page=provisional.urls()),
)
def test_cli_validate_command_with_edx_format(event):
    """Tests the validate command using the edx format."""

    event_str = event.json()
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-f", "edx"], input=event_str)
    assert event_str in result.output


def test_cli_convert_command_usage():
    """Tests ralph convert command usage."""

    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  From edX to xAPI converter options: \n"
        "    -u, --uuid-namespace TEXT     The UUID namespace to use for the `ID` field\n"
        "                                  generation\n"
        "    -p, --platform-url TEXT       The `actor.account.homePage` to use in the\n"
        "                                  xAPI statements  [required]\n"
        "  -f, --from [edx]                Input events format to convert  [required]\n"
        "  -t, --to [xapi]                 Output events format  [required]\n"
        "  -I, --ignore-errors             Continue writing regardless of raised errors\n"
        "  -F, --fail-on-unknown           Stop converting at first unknown event\n"
    ) in result.output

    result = runner.invoke(cli, ["convert"])
    assert result.exit_code > 0
    assert "Error: Missing option '-p' / '--platform-url'" in result.output


@settings(max_examples=1)
@given(
    st.builds(UIPageClose, referer=provisional.urls(), page=provisional.urls()),
)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_cli_convert_command_from_edx_to_xapi_format(valid_uuid, event):
    """Tests the convert command from edx to xapi format."""

    event_str = event.json()
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-v",
            "ERROR",
            "convert",
            "-f",
            "edx",
            "-t",
            "xapi",
            "-u",
            valid_uuid,
            "-p",
            "https://fun-mooc.fr",
        ],
        input=event_str,
    )
    assert result.exit_code == 0
    try:
        PageTerminated(**json.loads(result.output))
    except ValidationError as err:
        pytest.fail(f"Converted event is invalid: {err}")


@pytest.mark.parametrize("invalid_uuid", ["", None, 1, {}])
def test_cli_convert_command_with_invalid_uuid(invalid_uuid):
    """Tests that the convert command raises an exception when the uuid namespace is invalid."""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "convert",
            "-f",
            "edx",
            "-t",
            "xapi",
            "-u",
            invalid_uuid,
            "-p",
            "https://fun-mooc.fr",
        ],
    )
    assert result.exit_code > 0
    assert isinstance(result.exception, ConfigurationException)
    assert str(result.exception) == "Invalid UUID namespace"


@cli.command()
def dummy_verbosity_check():
    """Adding a dummy command to the cli with all logging levels."""

    test_logger.critical("CRITICAL")
    test_logger.error("ERROR")
    test_logger.warning("WARNING")
    test_logger.info("INFO")
    test_logger.debug("DEBUG")


@pytest.mark.parametrize("verbosity", ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"])
def test_cli_verbosity_option_should_impact_logging_behaviour(verbosity):
    """Tests that the verbosity option impacts logging output."""

    runner = CliRunner()
    result = runner.invoke(cli, ["-v", verbosity, "dummy-verbosity-check"])
    assert verbosity in result.output


def test_cli_fetch_command_usage():
    """Tests ralph fetch command usage."""

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
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
        "  es backend: \n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-index TEXT\n"
        "    --es-hosts TEXT\n"
        "  -b, --backend [es|ldp|fs|swift]\n"
        "                                  Backend  [required]\n"
        "  -c, --chunk-size INTEGER        Get events by chunks of size #\n"
    ) in result.output

    result = runner.invoke(cli, ["fetch"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. Choose from:\n\tes,\n\tldp,\n\tfs,\n\tswift\n"
        in result.output
    )


def test_cli_fetch_command_with_ldp_backend(monkeypatch):
    """Tests the fetch command using the LDP backend."""

    archive_content = {"foo": "bar"}

    def mock_read(this, name, chunk_size=500):
        """Always return the same archive."""
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


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_cli_fetch_command_with_fs_backend(fs, monkeypatch):
    """Tests the fetch command using the FS backend."""

    archive_content = {"foo": "bar"}

    def mock_read(this, name, chunk_size):
        """Always return the same archive."""
        # pylint: disable=unused-argument

        sys.stdout.buffer.write(bytes(json.dumps(archive_content), encoding="utf-8"))

    monkeypatch.setattr(FSStorage, "read", mock_read)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "fetch",
            "-b",
            "fs",
            "foo",
        ],
    )

    assert result.exit_code == 0
    assert '{"foo": "bar"}' in result.output


def test_cli_fetch_command_with_es_backend(es):
    """Tests ralph fetch command using the es backend."""
    # pylint: disable=invalid-name

    # Insert documents
    bulk(
        es,
        (
            {"_index": ES_TEST_INDEX, "_id": idx, "_source": {"id": idx}}
            for idx in range(10)
        ),
    )
    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "fetch",
            "-b",
            "es",
            "--es-hosts",
            ",".join(ES_TEST_HOSTS),
            "--es-index",
            ES_TEST_INDEX,
        ],
    )
    assert result.exit_code == 0
    assert "\n".join([json.dumps({"id": idx}) for idx in range(10)]) in result.output


def test_cli_list_command_usage():
    """Tests ralph list command usage."""

    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
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
        "  -b, --backend [ldp|fs|swift]    Backend  [required]\n"
        "  -n, --new / -a, --all           List not fetched (or all) archives\n"
        "  -D, --details / -I, --ids       Get archives detailed output (JSON)\n"
    ) in result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. Choose from:\n\tldp,\n\tfs,\n\tswift\n"
        in result.output
    )


def test_cli_list_command_with_ldp_backend(monkeypatch):
    """Tests the list command using the LDP backend."""

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
        """Mock LDP backend list method."""
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

    # List archives with detailed output
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


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_cli_list_command_with_fs_backend(fs, monkeypatch):
    """Tests the list command using the LDP backend."""

    archive_list = [
        "file1",
        "file2",
    ]
    archive_list_details = [
        {
            "filename": "file1",
            "modified_at": "1604661859",
            "size": 350,
        },
        {
            "filename": "file2",
            "created_at": "1604935848",
            "size": 25000,
        },
    ]

    def mock_list(this, details=False, new=False):
        """Mock LDP backend list method."""
        # pylint: disable=unused-argument

        response = archive_list
        if details:
            response = archive_list_details
        if new:
            response = response[1:]
        return response

    monkeypatch.setattr(FSStorage, "list", mock_list)

    runner = CliRunner()

    # List archives with default options
    result = runner.invoke(cli, ["list", "-b", "fs"])
    assert result.exit_code == 0
    assert "\n".join(archive_list) in result.output

    # List archives with detailed output
    result = runner.invoke(cli, ["list", "-b", "fs", "-D"])
    assert result.exit_code == 0
    assert (
        "\n".join(json.dumps(detail) for detail in archive_list_details)
        in result.output
    )

    # List new archives only
    result = runner.invoke(cli, ["list", "-b", "fs", "-n"])
    assert result.exit_code == 0
    assert "file2" in result.output
    assert "file1" not in result.output

    # Edge case: stream contains no archive
    monkeypatch.setattr(FSStorage, "list", lambda this, details, new: ())
    result = runner.invoke(cli, ["list", "-b", "fs"])
    assert result.exit_code == 0
    assert "Configured fs backend contains no archive" in result.output


# pylint: disable=invalid-name
def test_cli_push_command_with_fs_backend(fs):
    """Tests the push command using the FS backend."""

    fs.create_dir(str(APP_DIR))

    filename = Path("file1")
    file_path = FS_STORAGE_DEFAULT_PATH / filename

    # Create a file
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "push",
            "-b",
            "fs",
            "file1",
        ],
        input="test content",
    )

    assert result.exit_code == 0

    with file_path.open("r") as test_file:
        content = test_file.read()

    assert "test content" in content

    # Trying to create the same file without -f should raise an error
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "push",
            "-b",
            "fs",
            "file1",
        ],
        input="different content",
    )
    assert result.exit_code == 1
    assert "file1 already exists and overwrite is not allowed" in result.output

    # Try to create the same file with -f
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "push",
            "-b",
            "fs",
            "-f",
            "file1",
        ],
        input="different content",
    )

    assert result.exit_code == 0

    with file_path.open("r") as test_file:
        content = test_file.read()

    assert "different content" in content


def test_cli_push_command_with_es_backend(es):
    """Tests ralph push command using the es backend."""
    # pylint: disable=invalid-name

    # Documents
    records = [{"id": idx} for idx in range(10)]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "push",
            "-b",
            "es",
            "--es-hosts",
            ",".join(ES_TEST_HOSTS),
            "--es-index",
            ES_TEST_INDEX,
        ],
        input="\n".join(json.dumps(record) for record in records),
    )
    assert result.exit_code == 0

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)
    documents = list(scan(es, index=ES_TEST_INDEX, size=10))

    assert len(documents) == 10
    assert [document.get("_source") for document in documents] == records
