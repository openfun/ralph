"""Tests for Ralph graylog storage backend"""

import json
import sys
from io import StringIO

import pytest

from ralph.backends.logging.graylog import GraylogAPI, GraylogLogging
from ralph.defaults import (
    GRAYLOG_ADMIN_PASSWORD,
    GRAYLOG_ADMIN_USERNAME,
    GRAYLOG_HOST,
    GRAYLOG_PORT,
)


def test_backends_logging_graylog_logging_instantiation():
    """Tests the GraylogLogging backend instantiation."""
    # pylint: disable=protected-access

    logging = GraylogLogging(
        host=GRAYLOG_HOST,
        port=GRAYLOG_PORT,
        username=GRAYLOG_ADMIN_USERNAME,
        password=GRAYLOG_ADMIN_PASSWORD,
    )

    assert logging.name == "graylog"
    assert logging.host == "graylog"
    assert logging.port == 12201


@pytest.mark.parametrize("base_url", ["http://graylog:9000"])
@pytest.mark.parametrize("username", ["admin"])
@pytest.mark.parametrize("password", ["pass"])
@pytest.mark.parametrize(
    "headers",
    [
        {
            "X-Requested-By": "Ralph Malph",
            "Content-Type": "application/json",
        }
    ],
)
def test_graylog_api_good_instantiation(base_url, username, password, headers):
    """Tests the GraylogAPI instantiation."""

    api = GraylogAPI(
        base_url=base_url, username=username, password=password, headers=headers
    )

    assert api.base_url == "http://graylog:9000"
    assert api.username == "admin"
    assert api.password == "pass"


@pytest.mark.parametrize("base_url", ["http://graylog:9000"])
@pytest.mark.parametrize("username", ["admin"])
@pytest.mark.parametrize("password", ["pass"])
@pytest.mark.parametrize(
    "headers",
    [
        {
            "X-Requested-By": "Ralph Malph",
            "Content-Type": "application/json",
        }
    ],
)
def test_graylog_api_get_node_id_method(
    monkeypatch, base_url, username, password, headers
):
    """Tests that the `get_node_id` method returns the expected node UUID."""

    api = GraylogAPI(
        base_url=base_url, username=username, password=password, headers=headers
    )

    def mock_get(*args, **kwargs):
        """Always returns text attributes of a successful get method on '/api/cluster'
        endpoint.
        """
        # pylint: disable=unused-argument

        return json.dumps({"bc1c7764-5c7c-4cc0-92b9-ec2759ac1fa0": {"text": "foo"}})

    monkeypatch.setattr(GraylogAPI, "get", mock_get)
    result = api.get_node_id()

    assert result == "bc1c7764-5c7c-4cc0-92b9-ec2759ac1fa0"


def test_backends_logging_graylog_logging_send_method_should_activate_existing_input(
    monkeypatch,
):
    """Tests if a Graylog backend correctly activates a configured TCP input."""

    logging = GraylogLogging(
        host=GRAYLOG_HOST,
        port=GRAYLOG_PORT,
        username=GRAYLOG_ADMIN_USERNAME,
        password=GRAYLOG_ADMIN_PASSWORD,
    )

    def mock_get_node_id(*args, **kwargs):
        """Always returns a Graylog node id (of UUID type)."""
        # pylint: disable=unused-argument

        return "bc1c7764-5c7c-4cc0-92b9-ec2759ac1fa0"

    def mock_list_inputs(*args, **kwargs):
        """Returns the list of configured inputs in the case a TCP input has been
        configured.
        """
        # pylint: disable=unused-argument

        return {
            "inputs": [
                {
                    "title": "TCP input",
                    "global": False,
                    "name": "GELF TCP",
                    "created_at": "2021-11-22T19:29:42.622Z",
                    "type": "org.graylog2.inputs.gelf.tcp.GELFTCPInput",
                    "creator_user_id": "admin",
                    "attributes": {
                        "bind_address": "graylog",
                        "max_message_size": 2097152,
                        "number_worker_threads": 8,
                        "recv_buffer_size": 1048576,
                        "tls_client_auth": "disabled",
                        "tls_enable": False,
                        "use_null_delimiter": True,
                    },
                    "static_fields": {},
                    "node": "bc1c7764-5c7c-4cc0-92b9-ec2759ac1fa0",
                    "id": "619befa63f959f44ab2ce10a",
                }
            ],
            "total": 1,
        }

    def mock_activate_input(*args, **kwargs):
        """Always returns an input id."""
        # pylint: disable=unused-argument

        return json.dumps({"id": "619befa63f959f44ab2ce10a"})

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    )
    monkeypatch.setattr(logging.api, "get_node_id", mock_get_node_id)
    monkeypatch.setattr(logging.api, "list_inputs", mock_list_inputs)
    monkeypatch.setattr(logging.api, "activate_input", mock_activate_input)

    assert (
        logging.api.activate_input(
            input_id=logging.api.list_inputs().get("inputs")[0].get("id")
        )
        == '{"id": "619befa63f959f44ab2ce10a"}'
    )


def test_backends_logging_graylog_logging_send_method_should_launch_input_if_not_exist(
    monkeypatch,
):
    """Tests logging Graylog backend launches a given configured input if it is not
    already configured.
    """

    logging = GraylogLogging(
        host=GRAYLOG_HOST,
        port=GRAYLOG_PORT,
        username=GRAYLOG_ADMIN_USERNAME,
        password=GRAYLOG_ADMIN_PASSWORD,
    )

    def mock_get_node_id(*args, **kwargs):
        """Always returns a Graylog node id (of UUID type)."""
        # pylint: disable=unused-argument

        return "bc1c7764-5c7c-4cc0-92b9-ec2759ac1fa0"

    def mock_list_inputs(*args, **kwargs):
        """Returns the list of configured inputs in the case no input has been
        configured.
        """
        # pylint: disable=unused-argument

        return {"inputs": [], "total": 0}

    def mock_launch_input(*args, **kwargs):
        """Returns a dictionnary containing the id of a configured input newly
        created.
        """
        # pylint: disable=unused-argument

        return {"id": "61a0f59b1d3fab0f365fbba6"}

    def mock_activate_input(input_id, *args, **kwargs):
        """Always returns an input id."""
        # pylint: disable=unused-argument

        return json.dumps({"id": input_id})

    monkeypatch.setattr(
        "sys.stdin", StringIO("\n".join([json.dumps({"id": idx}) for idx in range(10)]))
    )
    monkeypatch.setattr(logging.api, "get_node_id", mock_get_node_id)
    monkeypatch.setattr(logging.api, "list_inputs", mock_list_inputs)
    monkeypatch.setattr(logging.api, "launch_input", mock_launch_input)
    monkeypatch.setattr(logging.api, "activate_input", mock_activate_input)

    assert (
        logging.api.activate_input(
            # pylint: disable=no-value-for-parameter
            input_id=logging.api.launch_input().get("id")
        )
        == '{"id": "61a0f59b1d3fab0f365fbba6"}'
    )


def test_backends_logging_graylog_logging_get_method_should_return_messages_by_chunk(
    monkeypatch,
):
    """Tests the `get` method of `GraylogLogging` backend returns logged messages."""

    logging = GraylogLogging(
        host=GRAYLOG_HOST,
        port=GRAYLOG_PORT,
        username=GRAYLOG_ADMIN_USERNAME,
        password=GRAYLOG_ADMIN_PASSWORD,
    )

    def mock_search_logs(*args, **kwargs):
        """Returns the logged messages."""
        # pylint: disable=unused-argument

        return json.dumps(
            {
                "messages": [
                    {"message": {"message": "message_1"}},
                    {"message": {"message": "message_2"}},
                    {"message": {"message": "message_3"}},
                    {"message": {"message": "message_4"}},
                ]
            }
        )

    monkeypatch.setattr(logging.api, "search_logs", mock_search_logs)

    output = []

    def mock_stdout_write(message, *args, **kwargs):
        """Appends a given message to a list each time it is called."""
        # pylint: disable=unused-argument

        return output.append(bytes(message))

    monkeypatch.setattr(sys.stdout.buffer, "write", mock_stdout_write)

    logging.get(chunk_size=2)

    assert len(output) == len(json.loads(mock_search_logs())["messages"])
