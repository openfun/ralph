"""Graylog storage backend for Ralph"""

import json
import logging
import sys
import urllib
from functools import cached_property

import requests
from logging_gelf.formatters import GELFFormatter
from logging_gelf.handlers import GELFTCPSocketHandler

from ...defaults import (
    GRAYLOG_ADMIN_PASSWORD,
    GRAYLOG_ADMIN_USERNAME,
    GRAYLOG_API_URL,
    GRAYLOG_HOST,
    GRAYLOG_INPUT_TITLE,
    GRAYLOG_INPUT_TYPE,
    GRAYLOG_PORT,
)
from ..mixins import HistoryMixin
from .base import BaseLogging

logger = logging.getLogger(__name__)


class GraylogAPI:
    """Defines Graylog API useful endpoints functions."""

    def __init__(self, base_url, username, password, headers):

        self.base_url = base_url
        self.username = username
        self.password = password
        self.headers = headers

    @property
    def _auth(self):
        return (self.username, self.password)

    def get(self, endpoint, params=None):
        """Perform Graylog API GET request."""

        with requests.get(
            urllib.parse.urljoin(self.base_url, endpoint),
            params=params,
            auth=self._auth,
            headers=self.headers,
            stream=True,
        ) as result:

            result.raise_for_status()

            yield result

    def post(self, endpoint, data):
        """Perform Graylog API POST request."""

        with requests.post(
            urllib.parse.urljoin(self.base_url, endpoint),
            auth=self._auth,
            headers=self.headers,
            json=data,
        ) as result:
            result.raise_for_status()

            yield result

    def put(self, endpoint, data):
        """Perform Graylog API PUT request."""

        with requests.put(
            urllib.parse.urljoin(self.base_url, endpoint),
            auth=self._auth,
            headers=self.headers,
            json=data,
        ) as result:
            result.raise_for_status()

            yield result

    def get_node_id(self):
        """Returns node id of the Graylog cluster."""

        return next(iter(json.loads(self.get(endpoint="/api/cluster"))))

    def list_inputs(self):
        """Returns list of the created inputs on the Graylog cluster."""

        return self.get("/api/system/inputs").text

    def create_input(self, data):
        """Creates a new input on the Graylog cluster."""

        return self.post("/api/system/inputs", data=data)

    def input_state(self, input_id):
        """Returns identified input with `given_id`."""

        return self.get(f"/api/system/inputstates/{input_id}").text

    def activate_input(self, input_id):
        """Activates a launched input."""

        return self.put(f"/api/system/inputstates/{input_id}")

    def search_logs(self, params):
        """Returns logs matching given `params` parameters."""

        return self.get("/api/search/universal/relative", params=params)


class GraylogLogging(HistoryMixin, BaseLogging):
    """Graylog logging backend"""

    # pylint: disable=too-many-arguments, too-many-instance-attributes

    name = "graylog"

    def __init__(
        self,
        host=GRAYLOG_HOST,
        port=GRAYLOG_PORT,
        username=GRAYLOG_ADMIN_USERNAME,
        password=GRAYLOG_ADMIN_PASSWORD,
        title=GRAYLOG_INPUT_TITLE,
        input_type=GRAYLOG_INPUT_TYPE,
        api_url=GRAYLOG_API_URL,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.title = title
        self.type = input_type
        self.api_url = api_url

        self.gelf_logger = logging.getLogger("gelf")
        self.gelf_logger.setLevel(logging.INFO)

        self.api = GraylogAPI(
            base_url=self.api_url,
            username=self.username,
            password=self.password,
            headers={
                "X-Requested-By": "Ralph Malph",
                "Content-Type": "application/json",
            },
        )

    @cached_property
    def input_configuration(self):
        """Returns configuration of the used input."""

        return {
            "bind_address": self.host,
            "max_message_size": 2097152,
            "number_worker_threads": 8,
            "port": int(self.port),
            "recv_buffer_size": 1048576,
            "tls_client_auth": "disabled",
            "tls_enable": False,
            "use_null_delimiter": True,
        }

    @cached_property
    def input(self):
        """Returns input configuration"""

        return {
            "node": self.api.get_node_id(),
            "configuration": self.input_configuration,
            "global": False,
            "title": self.title,
            "type": self.type,
        }

    def send(self, chunk_size=10, ignore_errors=False):
        """Send logs in graylog backend (one JSON event per line)."""

        logger.debug("Logging events (chunk size: %d)", chunk_size)

        inputs = json.loads(self.api.list_inputs())["inputs"]

        try:
            current_input = next(filter(lambda input: input["title"] == self.title, inputs))
        except StopIteration:
            current_input = json.loads(self.api.launch_input(data=self.input))
        self.api.activate_input(input_id=current_input.get("id"))

        handler = GELFTCPSocketHandler(host=self.host, port=self.port)
        handler.setFormatter(GELFFormatter())
        self.gelf_logger.addHandler(handler)

        for event in sys.stdin:
            self.gelf_logger.info(event)

    def get(self, chunk_size=10):
        """Read chunk_size records and stream them to stdout."""

        logger.debug("Fetching events (chunk_size: %d)", chunk_size)
        messages = json.loads(self.api.search_logs(params={"query": "*"}))["messages"]

        events = [message["message"]["message"] for message in messages]
        chunks = [events[i : i + chunk_size] for i in range(0, len(events), chunk_size)]

        for chunk in chunks:
            for event in chunk:
                sys.stdout.buffer.write(bytes(f"{event}" + "\n", encoding="utf-8"))
