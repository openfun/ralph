"""Tests for Ralph cli"""

import json
import sys
from pathlib import Path

from click.testing import CliRunner
from elasticsearch.helpers import bulk, scan

from ralph.backends.storage.fs import FSStorage
from ralph.backends.storage.ldp import LDPStorage
from ralph.cli import cli
from ralph.defaults import APP_DIR, FS_STORAGE_DEFAULT_PATH

from tests.fixtures.backends import ES_TEST_HOSTS, ES_TEST_INDEX


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
        "    --es-verify-certs / --no-es-verify-certs\n"
        "    --es-index TEXT\n"
        "    --es-hosts TEXT\n"
        "  -b, --backend [es|ldp|fs]       Backend  [required]\n"
        "  -c, --chunk-size INTEGER        Get events by chunks of size #"
    ) in result.output

    result = runner.invoke(cli, ["fetch"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'.  Choose from:\n\tes,\n\tldp,\n\tfs."
        in result.output
    )


def test_fetch_command_with_ldp_backend(monkeypatch):
    """Test the fetch command using the LDP backend"""

    archive_content = {"foo": "bar"}

    def mock_read(this, name, chunk_size=500):
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


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_fetch_command_with_fs_backend(fs, monkeypatch):
    """Test the fetch command using the FS backend"""

    archive_content = {"foo": "bar"}

    def mock_read(this, name, chunk_size):
        """Always return the same archive"""
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


def test_fetch_command_with_es_backend(es):
    """Test ralph fetch command using the es backend"""
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
        ["fetch", "-b", "es", "--es-hosts", ES_TEST_HOSTS, "--es-index", ES_TEST_INDEX],
    )
    assert result.exit_code == 0
    assert "\n".join([json.dumps({"id": idx}) for idx in range(10)]) in result.output


def test_list_command_usage():
    """Test ralph list command usage"""

    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  fs backend: \n"
        "    --fs-path TEXT\n"
        "  ldp backend: \n"
        "    --ldp-stream-id TEXT\n"
        "    --ldp-service-name TEXT\n"
        "    --ldp-consumer-key TEXT\n"
        "    --ldp-application-secret TEXT\n"
        "    --ldp-application-key TEXT\n"
        "    --ldp-endpoint TEXT\n"
        "  -b, --backend [ldp|fs]          Backend  [required]\n"
        "  -n, --new / -a, --all           List not fetched (or all) archives\n"
        "  -D, --details / -I, --ids       Get archives detailled output (JSON)\n"
    ) in result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'.  Choose from:\n\tldp,\n\tfs."
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


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_list_command_with_fs_backend(fs, monkeypatch):
    """Test the list command using the LDP backend"""

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
        """Mock LDP backend list method"""
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

    # List archives with detailled output
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
def test_push_command_with_fs_backend(fs):
    """Test the push command using the FS backend"""

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


def test_push_command_with_es_backend(es):
    """Test ralph push command using the es backend"""
    # pylint: disable=invalid-name

    # Documents
    records = [{"id": idx} for idx in range(10)]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["push", "-b", "es", "--es-hosts", ES_TEST_HOSTS, "--es-index", ES_TEST_INDEX],
        input="\n".join(json.dumps(record) for record in records),
    )

    assert result.exit_code == 0

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)
    documents = list(scan(es, index=ES_TEST_INDEX, size=10))

    assert len(documents) == 10
    assert [document.get("_source") for document in documents] == records
