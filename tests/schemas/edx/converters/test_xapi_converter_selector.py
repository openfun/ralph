"""Tests for the XapiConverterSelector class"""

import json
from io import StringIO

import pytest

from ralph.schemas.edx.converters.xapi_converter_selector import XapiConverterSelector

from tests.fixtures.logs import EventType

PLATFORM = "https://fun-mooc.fr"
CONVERTER = XapiConverterSelector(PLATFORM)


def convert(event, converter=CONVERTER):
    """Converts the string_event using CONVERTER and returns output as a list"""

    with StringIO() as file:
        file.write(json.dumps(event))
        file.seek(0)  # Don't forget to go back to file start before reading it!
        return list(converter.convert(file))


def test_convert_without_event_type_should_be_skipped():
    """Test that convert don't yield server events without event_type (they are invalid)"""

    invalid_server_event = {"event_source": "server"}
    assert convert(invalid_server_event) == []
    browser_event = {"event_source": "browser"}
    assert convert(browser_event) == []


def test_convert_with_invalid_event_source_should_be_skipped():
    """Test that convert don't yield any event when it's event_source is not browser nor event"""

    invalid_event = {"event_source": "not_server_nor_browser"}
    assert convert(invalid_event) == []


@pytest.mark.parametrize("event_source", ["server", "browser"])
def test_convert_with_invalid_context_should_be_skipped(event_source):
    """Test that convert don't yield events with invalid context"""

    # Missing context
    invalid_event = {
        "event_source": event_source,
        "event_type": "/some/path",
    }
    assert convert(invalid_event) == []

    # Context not a dict
    invalid_event = {
        "event_source": event_source,
        "event_type": "/some/path",
        "context": "not a dict",
    }
    assert convert(invalid_event) == []

    # Context missing path key
    invalid_event = {
        "event_source": event_source,
        "event_type": "/some/path",
        "context": {"not_path": "/some/value"},
    }
    assert convert(invalid_event) == []


@pytest.mark.parametrize(
    "event_type",
    [
        EventType.BROWSER_PROBLEM_CHECK,
        EventType.BROWSER_PROBLEM_GRADED,
        EventType.BROWSER_PROBLEM_RESET,
        EventType.BROWSER_PROBLEM_SAVE,
    ],
)
def test_convert_with_ignored_events_should_be_skipped(event_type, event):
    """Test that convert don't yield ignored events"""

    ignored_event = event(event_type)
    assert convert(ignored_event) == []
