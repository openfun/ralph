"""Tests for Ralph cli."""
import json
import logging
from pathlib import Path
from typing import Union

import pytest
from click.exceptions import BadParameter
from click.testing import CliRunner
from elasticsearch.helpers import bulk, scan
from hypothesis import settings as hypothesis_settings
from pydantic import ValidationError

from ralph.backends.conf import backends_settings
from ralph.backends.data.fs import FSDataBackend
from ralph.backends.data.ldp import LDPDataBackend
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
    """Test the CommaSeparatedKeyValueParamType custom parameter type."""
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
    """Test the CommaSeparatedTupleParamType parameter type with valid input."""
    param_type = CommaSeparatedTupleParamType()
    assert param_type.convert(value, None, None) == expected


@pytest.mark.parametrize("value", [None, {}, ["foo"], 10, True])
def test_cli_comma_separated_tuple_param_type_with_invalid_input(value):
    """Test the CommaSeparatedTupleParamType parameter type with invalid input."""
    param_type = CommaSeparatedTupleParamType()
    with pytest.raises(
        BadParameter,
        match="You should provide values separated by commas, e.g. foo,bar,baz",
    ):
        param_type.convert(value, None, None)


@pytest.mark.parametrize("value,expected", [('{"foo": "bar"}', {"foo": "bar"})])
def test_cli_json_string_param_type_with_valid_input(value, expected):
    """Test the JSONStringParamType custom parameter type with valid input."""
    param_type = JSONStringParamType()
    assert param_type.convert(value, None, None) == expected


@pytest.mark.parametrize("value", ["foo", None, {}])
def test_cli_json_string_param_type_with_invalid_input(value):
    """Test the JSONStringParamType custom parameter type with invalid input."""
    param_type = JSONStringParamType()
    with pytest.raises(
        BadParameter,
        match="You should provide a valid JSON string as input",
    ):
        param_type.convert(value, None, None)


def test_cli_help_option():
    """Test ralph --help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert (
        (
            "-v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO (default) or "
            "DEBUG"
        )
    ) in result.output


# pylint: disable=too-many-arguments
def _gen_cli_auth_args(
    username: str,
    password: str,
    scopes: list,
    ifi_command: str,
    ifi_value: Union[str, dict],
    agent_name: str = None,
    write: bool = False,
):
    """Generate arguments for cli to create user."""
    cli_args = ["auth", "-u", username, "-p", password]
    for scope in scopes:
        cli_args.extend(["-s", scope])
    cli_args.append(ifi_command)
    cli_args.extend(ifi_value.split())
    if agent_name:
        cli_args.extend(["-N", agent_name])
    if write:
        cli_args.append("-w")
    return cli_args


# pylint: disable=too-many-arguments
def _assert_matching_basic_auth_credentials(
    credentials: dict,
    username: str,
    scopes: list,
    ifi_type: str,
    ifi_value: Union[str, dict],
    agent_name: str = None,
    hash_: str = None,
):
    """Assert that credentials match other arguments.

    Args:
        credentials: credentials to match against
        username: username that should match credentials
        scopes: scopes that should match credentials
        ifi_type: type of ifi used in credentials. One of "mbox",
            "mbox_sha1sum", "openid", or "account"
        ifi_value: value of ifi
        agent_name: name to assign to agent. If None, no matching is performed
        hash: hash value of the password. If None, no matching is performed
    """
    assert credentials["username"] == username
    assert "hash" in credentials
    if hash_:
        assert credentials["hash"] == hash_
    assert sorted(credentials["scopes"]) == sorted(scopes)
    assert "agent" in credentials

    if agent_name is not None:
        assert credentials["agent"]["name"] == agent_name

    if "objectType" in credentials["agent"]:
        assert credentials["agent"]["objectType"] == "Agent"

    if ifi_type in ["mbox", "mbox_sha1sum", "openid"]:
        assert ifi_type in credentials["agent"]
        assert credentials["agent"][ifi_type] == ifi_value
    elif ifi_type == "account":
        assert "account" in credentials["agent"]
        assert "name" in credentials["agent"]["account"]
        assert "homePage" in credentials["agent"]["account"]
        assert credentials["agent"]["account"] == ifi_value
    else:
        raise ValueError(
            'ifi_type should be one of: "mbox", "mbox_sha1sum", "openid", "account"'
        )


def _ifi_type_from_command(ifi_command):
    """Return the ifi_type associated to the command being passed to cli."""
    if ifi_command not in ["-M", "-S", "-O", "-A"]:
        raise ValueError('The ifi_command must be one of: "-M", "-S", "-O", "-A"')

    return {"-M": "mbox", "-S": "mbox_sha1sum", "-O": "openid", "-A": "account"}[
        ifi_command
    ]


def _ifi_value_from_command(ifi_value, ifi_type):
    """Parse ifi_value returned by cli to generate dict when `ifi_type` is `account`."""
    if ifi_type == "account":
        # Parse arguments from cli
        return {"name": ifi_value.split()[0], "homePage": ifi_value.split()[1]}
    return ifi_value


@pytest.mark.parametrize(
    "scopes,ifi_command,ifi_value",
    [
        (["all"], "-M", "mailto:foo@bar.com"),  # mbox ifi
        (["all/read", "all"], "-M", "mailto:foo@bar.com"),
        (
            ["all"],
            "-S",
            "ebd31e95054c018b10727ccffd2ef2ec3a016ee9",
        ),  # mbox_sha1sum ifi
        (["all"], "-O", "http://foo.openid.example.org/"),  # mbox_openid ifi
        (["all"], "-A", "foo_name http://www.bar.xyz"),  # account ifi
    ],
)
def test_cli_auth_command_without_writing_auth_file(scopes, ifi_command, ifi_value):
    """Test ralph auth command when credentials are displayed in the tty."""

    username = "foo"
    password = "bar"
    agent_name = "foobarname"  # optional name

    cli_args = _gen_cli_auth_args(
        username,
        password,
        scopes,
        ifi_command,
        ifi_value,
        agent_name=agent_name,
        write=False,
    )

    runner = CliRunner()
    result = runner.invoke(cli, cli_args)

    assert result.exit_code == 0

    credentials = json.loads(result.output.split(".json", 1)[1].strip())

    ifi_type = _ifi_type_from_command(ifi_command=ifi_command)
    ifi_value = _ifi_value_from_command(ifi_value, ifi_type)

    _assert_matching_basic_auth_credentials(
        credentials=credentials,
        username=username,
        scopes=scopes,
        ifi_type=ifi_type,
        ifi_value=ifi_value,
        agent_name=agent_name,
    )


# pylint: disable=invalid-name,unused-argument
@pytest.mark.parametrize(
    "ifi_command_1, ifi_value_1, ifi_command_2, ifi_value_2",
    [
        (
            "-M",
            "mailto:foo@bar.com",
            "-S",
            "ebd31e95054c018b10727ccffd2ef2ec3a016ee9",
        ),  # mbox ifi
        (
            "-S",
            "ebd31e95054c018b10727ccffd2ef2ec3a016ee9",
            "-O",
            "http://foo.openid.example.org/",
        ),  # mbox_sha1sum ifi
        (
            "-O",
            "http://foo.openid.example.org/",
            "-A",
            "foo_name http://www.bar.xyz",
        ),  # mbox_openid ifi
        (
            "-A",
            "foo_name http://www.bar.xyz",
            "-M",
            "mailto:foo@bar.com",
        ),  # account ifi
    ],
)
# pylint: disable=too-many-locals
def test_cli_auth_command_when_writing_auth_file(
    fs, ifi_command_1, ifi_value_1, ifi_command_2, ifi_value_2
):
    """Test ralph auth command when credentials are written in the authentication
    file.
    """
    runner = CliRunner()

    username_1 = "foo"
    password_1 = "bar"
    scopes_1 = ["all"]

    # The authentication file does not exist

    # Add a first user
    cli_args = _gen_cli_auth_args(
        username_1, password_1, scopes_1, ifi_command_1, ifi_value_1, write=True
    )

    assert Path(settings.AUTH_FILE).exists() is False
    result = runner.invoke(cli, cli_args)
    assert result.exit_code == 0
    assert Path(settings.AUTH_FILE).exists() is True
    with Path(settings.AUTH_FILE).open(encoding="utf-8") as auth_file:
        all_credentials = json.loads("\n".join(auth_file.readlines()))
    assert len(all_credentials) == 1

    # Check that the first user matches
    ifi_type_1 = _ifi_type_from_command(ifi_command=ifi_command_1)
    ifi_value_1 = _ifi_value_from_command(ifi_value_1, ifi_type_1)
    _assert_matching_basic_auth_credentials(
        credentials=all_credentials[0],
        username=username_1,
        scopes=scopes_1,
        ifi_type=ifi_type_1,
        ifi_value=ifi_value_1,
    )

    # Add a second user
    username_2 = "lol"
    password_2 = "baz"
    scopes_2 = ["statements/write", "statements/read/mine"]

    cli_args = _gen_cli_auth_args(
        username_2, password_2, scopes_2, ifi_command_2, ifi_value_2, write=True
    )
    result = runner.invoke(cli, cli_args)

    assert result.exit_code == 0
    with Path(settings.AUTH_FILE).open(encoding="utf-8") as auth_file:
        all_credentials = json.loads("\n".join(auth_file.readlines()))
    assert len(all_credentials) == 2

    # Check that the first user still matches
    _assert_matching_basic_auth_credentials(
        credentials=all_credentials[0],
        username=username_1,
        scopes=scopes_1,
        ifi_type=ifi_type_1,
        ifi_value=ifi_value_1,
    )

    # Check that the second user matches
    ifi_type_2 = _ifi_type_from_command(ifi_command=ifi_command_2)
    ifi_value_2 = _ifi_value_from_command(ifi_value_2, ifi_type_2)
    _assert_matching_basic_auth_credentials(
        credentials=all_credentials[1],
        username=username_2,
        scopes=scopes_2,
        ifi_type=ifi_type_2,
        ifi_value=ifi_value_2,
    )


# pylint: disable=invalid-name
def test_cli_auth_command_when_writing_auth_file_with_incorrect_auth_file(fs):
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
    """Test ralph extract command using the GELF parser."""
    gelf_logger.info('{"username": "foo"}')

    runner = CliRunner()
    with Path(gelf_logger.handlers[0].stream.name).open(
        encoding=settings.LOCALE_ENCODING
    ) as log_file:
        gelf_content = log_file.read()
        result = runner.invoke(cli, ["extract", "-p", "gelf"], input=gelf_content)
        assert '{"username": "foo"}' in result.output


def test_cli_extract_command_with_es_parser():
    """Test ralph extract command using the ElasticSearchParser."""
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
    """Test ralph validate command using the edx format."""
    event_str = event.json()
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "-f", "edx"], input=event_str)
    assert event_str in result.output


@hypothesis_settings(deadline=None)
@custom_given(UIPageClose)
@pytest.mark.parametrize("valid_uuid", ["ee241f8b-174f-5bdb-bae9-c09de5fe017f"])
def test_cli_convert_command_from_edx_to_xapi_format(valid_uuid, event):
    """Test ralph convert command from edx to xapi format."""
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
    """Test that the ralph convert command raises an exception when the uuid namespace
    is invalid.
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
    """Test that the verbosity option impacts logging output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-v", verbosity, "dummy-verbosity-check"])
    assert verbosity in result.output


def test_cli_read_command_with_ldp_backend(monkeypatch):
    """Test ralph read command using the LDP backend."""
    archive_content = {"foo": "bar"}

    def mock_read(*_, **__):
        """Always return the same archive."""
        # pylint: disable=unused-argument

        yield bytes(json.dumps(archive_content), encoding="utf-8")

    monkeypatch.setattr(LDPDataBackend, "read", mock_read)

    runner = CliRunner()
    command = "read -b ldp --ldp-endpoint ovh-eu a547d9b3-6f2f-4913-a872-cf4efe699a66"
    result = runner.invoke(cli, command.split())

    assert result.exit_code == 0
    assert '{"foo": "bar"}' in result.output


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_cli_read_command_with_fs_backend(fs, monkeypatch):
    """Test ralph read command using the FS backend."""
    archive_content = {"foo": "bar"}

    def mock_read(*_, **__):
        """Always return the same archive."""

        yield bytes(json.dumps(archive_content), encoding="utf-8")

    monkeypatch.setattr(FSDataBackend, "read", mock_read)

    runner = CliRunner()
    result = runner.invoke(cli, "read -b fs foo".split())

    assert result.exit_code == 0
    assert '{"foo": "bar"}' in result.output


def test_cli_read_command_with_es_backend(es):
    """Test ralph read command using the es backend."""
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
    command = f"""-v ERROR read -b es --es-hosts {es_hosts}
        --es-default-index {ES_TEST_INDEX}
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


def test_cli_read_command_client_options_with_es_backend(es):
    """Test ralph read command with multiple client options using the es backend."""
    # pylint: disable=invalid-name

    runner = CliRunner()
    es_client_options = "ca_certs=/path/,verify_certs=True"
    command = f"""-v ERROR read -b es --es-client-options {es_client_options}"""
    result = runner.invoke(cli, command.split())
    assert result.exit_code == 1
    assert "TLS options require scheme to be 'https'" in str(result.exception)


def test_cli_read_command_with_es_backend_query(es):
    """Test ralph read command using the es backend and a query."""
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
    query = {"query": {"term": {"modulo": 0}}}
    query_str = json.dumps(query, separators=(",", ":"))

    command = (
        "-v ERROR "
        "read "
        "-b es "
        f"--es-hosts {es_hosts} "
        f"--es-default-index {ES_TEST_INDEX} "
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


def test_cli_read_command_with_ws_backend(events, ws):
    """Test ralph read command using the ws backend."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["read", "-b", "ws", "--ws-uri", f"ws://{WS_TEST_HOST}:{WS_TEST_PORT}"],
    )
    assert "\n".join([json.dumps(event) for event in events]) in result.output


def test_cli_list_command_with_ldp_backend(monkeypatch):
    """Test ralph list command using the LDP backend."""
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

    def mock_list(this, target=None, details=False, new=False):
        """Mock LDP backend list method."""
        # pylint: disable=unused-argument

        response = archive_list
        if details:
            response = archive_list_details
        if new:
            response = response[1:]
        return response

    monkeypatch.setattr(LDPDataBackend, "list", mock_list)

    runner = CliRunner()

    # List documents with default options
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu"])
    assert result.exit_code == 0
    assert "\n".join(archive_list) in result.output

    # List documents with detailed output
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu", "-D"])
    assert result.exit_code == 0
    assert (
        "\n".join(json.dumps(detail) for detail in archive_list_details)
        in result.output
    )

    # List new documents only
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu", "-n"])
    assert result.exit_code == 0
    assert "997db3eb-b9ca-485d-810f-b530a6cef7c6" in result.output
    assert "5d5c4c93-04a4-42c5-9860-f51fa4044aa1" not in result.output

    # Edge case: stream contains no document
    monkeypatch.setattr(LDPDataBackend, "list", lambda this, target, details, new: ())
    result = runner.invoke(cli, ["list", "-b", "ldp", "--ldp-endpoint", "ovh-eu"])
    assert result.exit_code == 0
    assert "Configured ldp backend contains no document" in result.output


# pylint: disable=invalid-name
# pylint: disable=unused-argument
def test_cli_list_command_with_fs_backend(fs, monkeypatch):
    """Test ralph list command using the LDP backend."""
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

    def mock_list(this, target=None, details=False, new=False):
        """Mock LDP backend list method."""
        # pylint: disable=unused-argument

        response = archive_list
        if details:
            response = archive_list_details
        if new:
            response = response[1:]
        return response

    monkeypatch.setattr(FSDataBackend, "list", mock_list)

    runner = CliRunner()

    # List documents with default options
    result = runner.invoke(cli, ["list", "-b", "fs"])
    assert result.exit_code == 0
    assert "\n".join(archive_list) in result.output

    # List documents with detailed output
    result = runner.invoke(cli, ["list", "-b", "fs", "-D"])
    assert result.exit_code == 0
    assert (
        "\n".join(json.dumps(detail) for detail in archive_list_details)
        in result.output
    )

    # List new documents only
    result = runner.invoke(cli, ["list", "-b", "fs", "-n"])
    assert result.exit_code == 0
    assert "file2" in result.output
    assert "file1" not in result.output

    # Edge case: stream contains no document
    monkeypatch.setattr(FSDataBackend, "list", lambda this, target, details, new: ())
    result = runner.invoke(cli, ["list", "-b", "fs"])
    assert result.exit_code == 0
    assert "Configured fs backend contains no document" in result.output


# pylint: disable=invalid-name
def test_cli_write_command_with_fs_backend(fs):
    """Test ralph write command using the FS backend."""
    fs.create_dir(str(settings.APP_DIR))
    fs.create_dir("foo")

    filename = Path("foo/file1")

    # Create a file
    runner = CliRunner()
    result = runner.invoke(
        cli,
        "write -b fs -t file1 --fs-default-directory-path foo".split(),
        input=b"test content",
    )

    assert result.exit_code == 0

    with filename.open("rb") as test_file:
        content = test_file.read()

    assert b"test content" in content

    # Trying to create the same file without -f should raise an error
    runner = CliRunner()
    result = runner.invoke(
        cli,
        "write -b fs -t file1 --fs-default-directory-path foo".split(),
        input=b"other content",
    )
    assert result.exit_code == 1
    assert "file1 already exists and overwrite is not allowed" in result.output

    # Try to create the same file with -f
    runner = CliRunner()
    result = runner.invoke(
        cli,
        "write -b fs -t file1 -f --fs-default-directory-path foo".split(),
        input=b"other content",
    )

    assert result.exit_code == 0

    with filename.open("rb") as test_file:
        content = test_file.read()

    assert b"other content" in content


def test_cli_write_command_with_es_backend(es):
    """Test ralph write command using the es backend."""
    # pylint: disable=invalid-name

    # Documents
    records = [{"id": idx} for idx in range(10)]

    runner = CliRunner()
    es_hosts = ",".join(ES_TEST_HOSTS)
    result = runner.invoke(
        cli,
        f"write -b es --es-hosts {es_hosts} --es-default-index {ES_TEST_INDEX}".split(),
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
    """Test the ralph runserver command should consider the host and port arguments."""

    def mock_uvicorn_run(_, host=None, port=None, **kwargs):
        """Mock uvicorn.run asserting host and port values."""
        assert host == host_
        assert port == int(port_)

    monkeypatch.setattr("ralph.cli.uvicorn.run", mock_uvicorn_run)

    runner = CliRunner()
    result = runner.invoke(cli, f"runserver -h {host_} -p {port_} -b es".split())
    assert result.exit_code == 0
    assert f"Running API server on {host_}:{port_} with es backend" in result.output


def test_cli_runserver_command_environment_file_generation(monkeypatch):
    """Test the ralph runserver command should create the expected environment file."""

    def mock_uvicorn_run(_, env_file=None, **kwargs):
        """Mock uvicorn.run asserting environment file content."""
        with open(env_file, mode="r", encoding=settings.LOCALE_ENCODING) as file:
            env_lines = [
                f"RALPH_RUNSERVER_BACKEND={settings.RUNSERVER_BACKEND}\n",
                "RALPH_BACKENDS__LRS__ES__DEFAULT_INDEX=foo\n",
                "RALPH_BACKENDS__LRS__ES__CLIENT_OPTIONS__verify_certs=True\n",
                "RALPH_BACKENDS__LRS__MONGO__DEFAULT_CHUNK_SIZE="
                f"{backends_settings.BACKENDS.LRS.MONGO.DEFAULT_CHUNK_SIZE}\n",
                "RALPH_BACKENDS__LRS__MONGO__DEFAULT_COLLECTION="
                f"{backends_settings.BACKENDS.LRS.MONGO.DEFAULT_COLLECTION}\n",
                "RALPH_BACKENDS__LRS__MONGO__DEFAULT_DATABASE="
                f"{backends_settings.BACKENDS.LRS.MONGO.DEFAULT_DATABASE}\n",
                "RALPH_BACKENDS__LRS__MONGO__CONNECTION_URI="
                f"{backends_settings.BACKENDS.LRS.MONGO.CONNECTION_URI}\n",
                "RALPH_BACKENDS__LRS__FS__DEFAULT_LRS_FILE="
                f"{backends_settings.BACKENDS.LRS.FS.DEFAULT_LRS_FILE}\n",
                "RALPH_BACKENDS__LRS__FS__DEFAULT_QUERY_STRING="
                f"{backends_settings.BACKENDS.LRS.FS.DEFAULT_QUERY_STRING}\n",
                "RALPH_BACKENDS__LRS__FS__DEFAULT_DIRECTORY_PATH="
                f"{backends_settings.BACKENDS.LRS.FS.DEFAULT_DIRECTORY_PATH}\n",
                "RALPH_BACKENDS__LRS__FS__DEFAULT_CHUNK_SIZE="
                f"{backends_settings.BACKENDS.LRS.FS.DEFAULT_CHUNK_SIZE}\n",
                "RALPH_BACKENDS__LRS__ES__POINT_IN_TIME_KEEP_ALIVE="
                f"{backends_settings.BACKENDS.LRS.ES.POINT_IN_TIME_KEEP_ALIVE}\n",
                "RALPH_BACKENDS__LRS__ES__HOSTS="
                f"{','.join(backends_settings.BACKENDS.LRS.ES.HOSTS)}\n",
                "RALPH_BACKENDS__LRS__ES__DEFAULT_CHUNK_SIZE="
                f"{backends_settings.BACKENDS.LRS.ES.DEFAULT_CHUNK_SIZE}\n",
                "RALPH_BACKENDS__LRS__ES__ALLOW_YELLOW_STATUS="
                f"{backends_settings.BACKENDS.LRS.ES.ALLOW_YELLOW_STATUS}\n",
                "RALPH_BACKENDS__LRS__CLICKHOUSE__IDS_CHUNK_SIZE="
                f"{backends_settings.BACKENDS.LRS.CLICKHOUSE.IDS_CHUNK_SIZE}\n",
                "RALPH_BACKENDS__LRS__CLICKHOUSE__DEFAULT_CHUNK_SIZE="
                f"{backends_settings.BACKENDS.LRS.CLICKHOUSE.DEFAULT_CHUNK_SIZE}\n",
                "RALPH_BACKENDS__LRS__CLICKHOUSE__EVENT_TABLE_NAME="
                f"{backends_settings.BACKENDS.LRS.CLICKHOUSE.EVENT_TABLE_NAME}\n",
                "RALPH_BACKENDS__LRS__CLICKHOUSE__DATABASE="
                f"{backends_settings.BACKENDS.LRS.CLICKHOUSE.DATABASE}\n",
                "RALPH_BACKENDS__LRS__CLICKHOUSE__PORT="
                f"{backends_settings.BACKENDS.LRS.CLICKHOUSE.PORT}\n",
                "RALPH_BACKENDS__LRS__CLICKHOUSE__HOST="
                f"{backends_settings.BACKENDS.LRS.CLICKHOUSE.HOST}\n",
            ]
            env_lines_created = file.readlines()
            assert all(line in env_lines_created for line in env_lines)

    monkeypatch.setattr("ralph.cli.uvicorn.run", mock_uvicorn_run)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        "runserver -b es --es-default-index foo "
        "--es-client-options verify_certs=True".split(),
    )
    assert result.exit_code == 0
