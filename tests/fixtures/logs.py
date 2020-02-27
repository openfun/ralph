"""
Logs format pytest fixtures.
"""
import logging
from secrets import token_hex
from tempfile import NamedTemporaryFile

import pandas as pd
import pytest
from djehouty.libgelf.formatters import GELFFormatter
from faker import Faker

FAKE = Faker()


@pytest.fixture
def gelf_logger():
    """Generate a GELF logger to generate wrapped tracking log fixtures."""

    handler = logging.StreamHandler(NamedTemporaryFile(mode="w+", delete=False))
    handler.setLevel(logging.INFO)
    handler.setFormatter(GELFFormatter(null_character=False))

    # Generate a unique logger per test function to avoid stacking handlers on
    # the same one
    logger = logging.getLogger(f"test_logger_{token_hex(8)}")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def server_event(size):
    """Returns event_number of events of event_type server"""
    return pd.DataFrame(
        data=[
            {
                "username": FAKE.profile().get("username"),
                "event_type": FAKE.uri_path(),
                "ip": FAKE.ipv4_public(),
                "agent": FAKE.user_agent(),
                "host": FAKE.hostname(),  # not really as the host is the docker container ID
                "referer": FAKE.url(),
                "accept_language": FAKE.locale(),  # could be also something like "en-US,en;q=0.5"
                "event": '{"POST": {}, "GET": {}}',
                "event_source": "server",
                "context": {
                    "course_user_tags": {},
                    "user_id": FAKE.random_digit_or_empty(),
                    "org_id": FAKE.word(),
                    "course_id": "{}+{}+{}".format(
                        FAKE.word(), FAKE.word(), FAKE.word()
                    ),
                    "path": FAKE.uri_path(),  # "event_type" and "context:path" share the same URI
                },
                "time": FAKE.iso8601(),
                "page": "null",
            }
            for i in range(size)
        ]
    )


def browser_event(size):
    """Returns event_number of events of event_type browser"""
    return pd.DataFrame(
        data=[
            {
                "username": FAKE.profile().get("username"),
                "event_source": "browser",
                "name": "page_close",
                "accept_language": FAKE.locale(),  # could be also something like "en-US,en;q=0.5"
                "time": FAKE.iso8601(),
                "agent": FAKE.user_agent(),
                "page": FAKE.url(),
                "host": FAKE.hostname(),  # not really as the host is the docker container ID
                "session": FAKE.md5(raw_output=False),
                "referer": FAKE.url(),
                "context": {
                    "user_id": FAKE.random_digit_or_empty(),
                    "org_id": FAKE.word(),
                    "course_id": "{}+{}+{}".format(
                        FAKE.word(), FAKE.word(), FAKE.word()
                    ),
                    "path": "/event",
                },
                "ip": FAKE.ipv4_public(),
                "event": "{}",
                "event_type": "page_close",  # could be an other sting too
            }
            for i in range(size)
        ]
    )


EVENT_TYPES = {
    "server": server_event,
    "browser": browser_event,
}


@pytest.fixture
def event():
    """Returns an event generator that generates event_number of events of the given event_type"""

    def _event(size, event_type="server"):
        return EVENT_TYPES.get(event_type, server_event)(size)

    return _event
