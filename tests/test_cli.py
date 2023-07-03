"""Tests for Ralph cli."""
import json
import logging
from pathlib import Path

import pytest
from click.exceptions import BadParameter
from click.testing import CliRunner
from elasticsearch.helpers import bulk, scan
from hypothesis import settings as hypothesis_settings
from pydantic import ValidationError

from ralph.backends.storage.fs import FSStorage
from ralph.backends.storage.ldp import LDPStorage
from ralph.cli import (
    CommaSeparatedKeyValueParamType,
    CommaSeparatedTupleParamType,
    JSONStringParamType,
    cli,
)
from ralph.conf import settings
from ralph.exceptions import ConfigurationException
from ralph.models.edx.navigational.statements import UIPageClose
from ralph.models.xapi.navigation.statements import PageTerminated

from tests.fixtures.backends import (
    ES_TEST_HOSTS,
    ES_TEST_INDEX,
    WS_TEST_HOST,
    WS_TEST_PORT,
)
from tests.fixtures.hypothesis_strategies import custom_given

test_logger = logging.getLogger("ralph")


def test_cli_comma_separated_key_value_param_type():
    """Tests the CommaSeparatedKeyValueParamType custom parameter type."""
    param_type = CommaSeparatedKeyValueParamType()

    # Bad options
    with pytest.raises(
        BadParameter,
        match=(
            "You should provide key=value pairs separated by commas, "
            "e.g. foo=bar,bar=2"
        ),
    ):
        param_type.convert("foo=bar,baz", None, None)
    with pytest.raises(
        BadParameter,
        match=(
            "You should provide key=value pairs separated by commas, "
            "e.g. foo=bar,bar=2"
        ),
    ):
        param_type.convert("foo=bar,", None, None)

    # Option already a dictionary (from defaults)
    assert param_type.convert({"foo": "bar"}, None, None) == {"foo": "bar"}

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


@pytest.mark.parametrize(
    "value,expected",
    [
        ("foo", ("foo",)),
        ("foo,bar", ("foo", "bar")),
        ("foo,bar,baz", ("foo", "bar", "baz")),
        (("foo", "bar", "baz"), ("foo", "bar", "baz")),
    ],
)
def test_cli_comma_separated_tuple_param_type_with_valid_input(value, expected):
    """Tests the CommaSeparatedTupleParamType parameter type with valid input."""
    param_type = CommaSeparatedTupleParamType()
    assert param_type.convert(value, None, None) == expected


@pytest.mark.parametrize("value", [None, {}, ["foo"], 10, True])
def test_cli_comma_separated_tuple_param_type_with_invalid_input(value):
    """Tests the CommaSeparatedTupleParamType parameter type with invalid input."""
    param_type = CommaSeparatedTupleParamType()
    with pytest.raises(
        BadParameter,
        match="You should provide values separated by commas, e.g. foo,bar,baz",
    ):
        param_type.convert(value, None, None)


@pytest.mark.parametrize("value,expected", [('{"foo": "bar"}', {"foo": "bar"})])
def test_cli_json_string_param_type_with_valid_input(value, expected):
    """Tests the JSONStringParamType custom parameter type with valid input."""
    param_type = JSONStringParamType()
    assert param_type.convert(value, None, None) == expected


@pytest.mark.parametrize("value", ["foo", None, {}])
def test_cli_json_string_param_type_with_invalid_input(value):
    """Tests the JSONStringParamType custom parameter type with invalid input."""
    param_type = JSONStringParamType()
    with pytest.raises(
        BadParameter,
        match="You should provide a valid JSON string as input",
    ):
        param_type.convert(value, None, None)


def test_cli_help_option():
    """Tests ralph --help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert (
        (
            "-v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO (default) or "
            "DEBUG"
        )
    ) in result.output


def test_cli_auth_command_without_writing_auth_file():
    """Test ralph auth command when credentials are displayed in the tty."""
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "-u", "foo", "-p", "bar", "-s", "foo_scope"])

    assert result.exit_code == 0

    credentials = json.loads("".join(result.output.split("\n")[-8:-1]))
    assert credentials["username"] == "foo"
    assert "hash" in credentials
    assert len(credentials["scopes"]) == 1
    assert credentials["scopes"][0] == "foo_scope"

    # Test multiple scopes
    result = runner.invoke(
        cli, ["auth", "-u", "foo", "-p", "bar", "-s", "foo_scope", "-s", "admin_scope"]
    )

    assert result.exit_code == 0

    credentials = json.loads("".join(result.output.split("\n")[-9:-1]))
    assert credentials["username"] == "foo"
    assert "hash" in credentials
    assert len(credentials["scopes"]) == 2
    assert credentials["scopes"][0] == "foo_scope"
    assert credentials["scopes"][1] == "admin_scope"


# pylint: disable=invalid-name,unused-argument
def test_cli_auth_command_when_writing_auth_file(fs):
    """Test ralph auth command when credentials are written in the authentication
    file.
    """
    runner = CliRunner()

    # The authentication file does not exist
    assert Path(settings.AUTH_FILE).exists() is False
    result = runner.invoke(
        cli, ["auth", "-u", "foo", "-p", "bar", "-s", "foo_scope", "-w"]
    )
    assert result.exit_code == 0
    assert Path(settings.AUTH_FILE).exists() is True
    with Path(settings.AUTH_FILE).open(encoding="utf-8") as auth_file:
        all_credentials = json.loads("\n".join(auth_file.readlines()))
    assert len(all_credentials) == 1
    credentials = all_credentials[0]
    assert credentials["username"] == "foo"
    assert "hash" in credentials
    assert len(credentials["scopes"]) == 1
    assert credentials["scopes"][0] == "foo_scope"

    # Add a new user
    result = runner.invoke(
        cli,
        [
            "auth",
            "-u",
            "lol",
            "-p",
            "baz",
            "-s",
            "lol_scope",
            "-s",
            "admin_scope",
            "-w",
        ],
    )
    assert result.exit_code == 0
    with Path(settings.AUTH_FILE).open(encoding="utf-8") as auth_file:
        all_credentials = json.loads("\n".join(auth_file.readlines()))
    assert len(all_credentials) == 2
    credentials = all_credentials[0]
    assert credentials["username"] == "foo"
    assert "hash" in credentials
    assert len(credentials["scopes"]) == 1
    assert credentials["scopes"][0] == "foo_scope"
    credentials = all_credentials[1]
    assert credentials["username"] == "lol"
    assert "hash" in credentials
    assert len(credentials["scopes"]) == 2
    assert credentials["scopes"][0] == "lol_scope"
    assert credentials["scopes"][1] == "admin_scope"


# pylint: disable=invalid-name
def test_cli_auth_command_when_writing_auth_file_whith_incorrect_auth_file(fs):
    """Test ralph auth command when credentials are written in the authentication
    file with a badly formatted original authentication file.
    """
    runner = CliRunner()

    # Create the base auth file path in the fake fs with badly formatted JSON
    # file content
    contents = (
        "{\n"
        ' "username": "johndoe",\n'
        ' "hash": "secretlynothashed",\n'
        ' "scope": ["johndoe_scope"]\n'
    )
    fs.create_file(settings.AUTH_FILE, contents=contents)

    result = runner.invoke(
        cli, ["auth", "-u", "foo", "-p", "bar", "-s", "foo_scope", "-w"]
    )
    assert result.exit_code > 0
    auth_file = Path(settings.AUTH_FILE)
    assert auth_file.exists() is True
    assert auth_file.read_text(encoding="utf-8") == contents


def test_cli_extract_command_with_gelf_parser(gelf_logger):
    """Tests the extract command using the GELF parser."""
    gelf_logger.info('{"username": "foo"}')

    runner = CliRunner()
    with Path(gelf_logger.handlers[0].stream.name).open(
        encoding=settings.LOCALE_ENCODING
    ) as log_file:
        gelf_content = log_file.read()
        result = runner.invoke(cli, ["extract", "-p", "gelf"], input=gelf_content)
        assert '{"username": "foo"}' in result.output


def test_cli_extract_command_with_es_parser():
    """Tests the extract command using the ElasticSearchParser."""
    es_output = (
        "\n".join(
            [
                json.dumps(
                    {
                        "_index": ES_TEST_INDEX,
                        "_id": str(idx),
                        "_score": None,
                        "_source": {"id": idx},
                        "sort": [idx],
                    }
                )
                for idx in range(10)
            ]
        )
        + "\n"
    )

    runner = CliRunner()
    result = runner.invoke(cli, "extract -p es".split(), input=es_output)
    assert result.exit_code == 0
    assert "\n".join([json.dumps({"id": idx}) for idx in range(10)]) in result.output


@custom_given(UIPageClose)
def test_cli_validate_command_with_edx_format(event):
    """Tests the validate command using the edx format."""
    event_str = event.json()
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-f", "edx"], input=event_str)
    assert event_str in result.output


@hypothesis_settings(deadline=None)
@custom_given(UIPageClose)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_cli_convert_command_from_edx_to_xapi_format(valid_uuid, event):
    """Tests the convert command from edx to xapi format."""
    event_str = event.json()
    runner = CliRunner()
    command = f"-v ERROR convert -f edx -t xapi -u {valid_uuid} -p https://fun-mooc.fr"
    result = runner.invoke(cli, command.split(), input=event_str)
    assert result.exit_code == 0
    try:
        PageTerminated(**json.loads(result.output))
    except ValidationError as err:
        pytest.fail(f"Converted event is invalid: {err}")


@pytest.mark.parametrize("invalid_uuid", ["", None, 1, {}])
def test_cli_convert_command_with_invalid_uuid(invalid_uuid):
    """Tests that the convert command raises an exception when the uuid namespace is
    invalid.
    """
    runner = CliRunner()
    command = f"convert -f edx -t xapi -u '{invalid_uuid}' -p https://fun-mooc.fr"
    result = runner.invoke(cli, command.split())
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


def test_cli_fetch_command_with_ldp_backend(monkeypatch):
    """Tests the fetch command using the LDP backend."""
    archive_content = {"foo": "bar"}

    def mock_read(this, name, chunk_size=500):
        """Always return the same archive."""
        # pylint: disable=unused-argument

        yield bytes(json.dumps(archive_content), encoding="utf-8")

    monkeypatch.setattr(LDPStorage, "read", mock_read)

    runner = CliRunner()
    command = "fetch -b ldp --ldp-endpoint ovh-eu a547d9b3-6f2f-4913-a872-cf4efe699a66"
    result = runner.invoke(cli, command.split())

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

        yield bytes(json.dumps(archive_content), encoding="utf-8")

    monkeypatch.setattr(FSStorage, "read", mock_read)

    runner = CliRunner()
    result = runner.invoke(cli, "fetch -b fs foo".split())

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
    es_hosts = ",".join(ES_TEST_HOSTS)
    es_client_options = "verify_certs=True"
    command = f"""-v ERROR fetch -b es --es-hosts {es_hosts} --es-index {ES_TEST_INDEX}
        --es-client-options {es_client_options}"""
    result = runner.invoke(cli, command.split())
    assert result.exit_code == 0
    expected = (
        "\n".join(
            [
                json.dumps(
                    {
                        "_index": ES_TEST_INDEX,
                        "_id": str(idx),
                        "_score": None,
                        "_source": {"id": idx},
                        "sort": [idx],
                    }
                )
                for idx in range(10)
            ]
        )
        + "\n"
    )

    assert expected == result.output


def test_cli_fetch_command_client_options_with_es_backend(es):
    """Tests ralph fetch command with multiple client options using the es backend."""
    # pylint: disable=invalid-name

    runner = CliRunner()
    es_client_options = "ca_certs=/path/,verify_certs=True"
    command = f"""-v ERROR fetch -b es --es-client-options {es_client_options}"""
    result = runner.invoke(cli, command.split())
    assert result.exit_code == 1
    assert "TLS options require scheme to be 'https'" in str(result.exception)


def test_cli_fetch_command_with_es_backend_query(es):
    """Tests ralph fetch command using the es backend and a query."""
    # pylint: disable=invalid-name

    # Insert documents
    bulk(
        es,
        (
            {
                "_index": ES_TEST_INDEX,
                "_id": idx,
                "_source": {"id": idx, "modulo": idx % 2},
            }
            for idx in range(10)
        ),
    )
    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)

    runner = CliRunner()
    es_hosts = ",".join(ES_TEST_HOSTS)
    query = {"query": {"query": {"term": {"modulo": 0}}}}
    query_str = json.dumps(query, separators=(",", ":"))

    command = (
        "-v ERROR "
        "fetch "
        "-b es "
        f"--es-hosts {es_hosts} "
        f"--es-index {ES_TEST_INDEX} "
        f"--query {query_str}"
    )
    result = runner.invoke(cli, command.split())
    assert result.exit_code == 0
    expected = (
        "\n".join(
            [
                json.dumps(
                    {
                        "_index": ES_TEST_INDEX,
                        "_id": str(idx),
                        "_score": None,
                        "_source": {"id": idx, "modulo": 0},
                        "sort": [idx],
                    }
                )
                for idx in range(0, 10, 2)
            ]
        )
        + "\n"
    )

    assert expected == result.output


def test_cli_fetch_command_with_ws_backend(events, ws):
    """Tests ralph fetch command using the ws backend."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["fetch", "-b", "ws", "--ws-uri", f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}"],
    )
    assert "\n".join([json.dumps(event) for event in events]) in result.output


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
            "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
            "size": 67906662,
        },
        {
            "archiveId": "997db3eb-b9ca-485d-810f-b530a6cef7c6",
            "createdAt": "2020-06-18T04:38:59.436634+02:00",
            "filename": "2020-06-17.gz",
            "md5": "01585b394be0495e38dbb60b20cb40a9",
            "retrievalDelay": 0,
            "retrievalState": "sealed",
            "sha256": "645d8e21e6fdb8aa7ffc5c[...]9ce612d06df8dcf67cb29a45ca",
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
    fs.create_dir(str(settings.APP_DIR))

    filename = Path("file1")
    file_path = Path(settings.BACKENDS.STORAGE.FS.PATH) / filename

    # Create a file
    runner = CliRunner()
    result = runner.invoke(cli, "push -b fs file1".split(), input="test content")

    assert result.exit_code == 0

    with file_path.open("r", encoding=settings.LOCALE_ENCODING) as test_file:
        content = test_file.read()

    assert "test content" in content

    # Trying to create the same file without -f should raise an error
    runner = CliRunner()
    result = runner.invoke(cli, "push -b fs file1".split(), input="other content")
    assert result.exit_code == 1
    assert "file1 already exists and overwrite is not allowed" in result.output

    # Try to create the same file with -f
    runner = CliRunner()
    result = runner.invoke(cli, "push -b fs -f file1".split(), input="other content")

    assert result.exit_code == 0

    with file_path.open("r", encoding=settings.LOCALE_ENCODING) as test_file:
        content = test_file.read()

    assert "other content" in content


def test_cli_push_command_with_es_backend(es):
    """Tests ralph push command using the es backend."""
    # pylint: disable=invalid-name

    # Documents
    records = [{"id": idx} for idx in range(10)]

    runner = CliRunner()
    es_hosts = ",".join(ES_TEST_HOSTS)
    result = runner.invoke(
        cli,
        f"push -b es --es-hosts {es_hosts} --es-index {ES_TEST_INDEX}".split(),
        input="\n".join(json.dumps(record) for record in records),
    )
    assert result.exit_code == 0

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)
    documents = list(scan(es, index=ES_TEST_INDEX, size=10))

    assert len(documents) == 10
    assert [document.get("_source") for document in documents] == records


@pytest.mark.parametrize("host_,port_", [("0.0.0.0", "8000"), ("127.0.0.1", "80")])
def test_cli_runserver_command_with_host_and_port_arguments(host_, port_, monkeypatch):
    """Tests the ralph runserver command should consider the host and port arguments."""

    def mock_uvicorn_run(_, host=None, port=None, **kwargs):
        """Mocks uvicorn.run asserting host and port values."""
        assert host == host_
        assert port == int(port_)

    monkeypatch.setattr("ralph.cli.uvicorn.run", mock_uvicorn_run)

    runner = CliRunner()
    result = runner.invoke(cli, f"runserver -h {host_} -p {port_} -b es".split())
    assert result.exit_code == 0
    assert f"Running API server on {host_}:{port_} with es backend" in result.output


def test_cli_runserver_command_environment_file_generation(monkeypatch):
    """Tests the ralph runserver command should create the expected environment file."""

    def mock_uvicorn_run(_, env_file=None, **kwargs):
        """Mocks uvicorn.run asserting environment file content."""
        with open(env_file, mode="r", encoding=settings.LOCALE_ENCODING) as file:
            env_lines = [
                f"RALPH_RUNSERVER_BACKEND={settings.RUNSERVER_BACKEND}\n",
                "RALPH_BACKENDS__DATABASE__ES__INDEX=foo\n",
                "RALPH_BACKENDS__DATABASE__ES__CLIENT_OPTIONS__verify_certs=True\n",
                "RALPH_BACKENDS__DATABASE__CLICKHOUSE__EVENT_TABLE_NAME="
                f"{settings.BACKENDS.DATABASE.CLICKHOUSE.EVENT_TABLE_NAME}\n",
                "RALPH_BACKENDS__DATABASE__CLICKHOUSE__DATABASE="
                f"{settings.BACKENDS.DATABASE.CLICKHOUSE.DATABASE}\n",
                "RALPH_BACKENDS__DATABASE__CLICKHOUSE__PORT="
                f"{settings.BACKENDS.DATABASE.CLICKHOUSE.PORT}\n",
                "RALPH_BACKENDS__DATABASE__CLICKHOUSE__HOST="
                f"{settings.BACKENDS.DATABASE.CLICKHOUSE.HOST}\n",
                "RALPH_BACKENDS__DATABASE__MONGO__COLLECTION="
                f"{settings.BACKENDS.DATABASE.MONGO.COLLECTION}\n",
                "RALPH_BACKENDS__DATABASE__MONGO__DATABASE="
                f"{settings.BACKENDS.DATABASE.MONGO.DATABASE}\n",
                "RALPH_BACKENDS__DATABASE__MONGO__CONNECTION_URI="
                f"{settings.BACKENDS.DATABASE.MONGO.CONNECTION_URI}\n",
                "RALPH_BACKENDS__DATABASE__ES__OP_TYPE="
                f"{settings.BACKENDS.DATABASE.ES.OP_TYPE}\n",
                "RALPH_BACKENDS__DATABASE__ES__HOSTS="
                f"{','.join(settings.BACKENDS.DATABASE.ES.HOSTS)}\n",
            ]
            assert file.readlines() == env_lines

    monkeypatch.setattr("ralph.cli.uvicorn.run", mock_uvicorn_run)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        "runserver -b es --es-index foo --es-client-options verify_certs=True".split(),
    )
    assert result.exit_code == 0
