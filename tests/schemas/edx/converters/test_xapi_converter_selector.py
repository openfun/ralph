"""Tests for the XapiConverterSelector class"""

import json
from io import StringIO

from ralph.schemas.edx.converters.xapi_converter_selector import XapiConverterSelector

PLATFORM = "https://fun-mooc.fr"
CONVERTER = XapiConverterSelector(PLATFORM)


def convert(event, converter=CONVERTER):
    """Converts the string_event using CONVERTER and returns output as a list"""

    with StringIO() as file:
        file.write(json.dumps(event))
        file.seek(0)  # Don't forget to go back to file start before reading it!
        return list(converter.convert(file))


def test_convert_with_browser_event():
    """Test that convert don't yield browser events (we don't support them for now)"""

    browser_event = {"event_source": "browser"}
    assert convert(browser_event) == []


def test_convert_with_server_event_without_event_type():
    """Test that convert don't yield server events without event_type (they are invalid)"""

    invalid_server_event = {"event_source": "server"}
    assert convert(invalid_server_event) == []


def test_convert_with_server_event_with_invalid_context():
    """Test that convert don't yield server events with invalid context"""

    # Missing context
    invalid_server_event = {
        "event_source": "server",
        "event_type": "/some/path",
    }
    assert convert(invalid_server_event) == []

    # Context not a dict
    invalid_server_event = {
        "event_source": "server",
        "event_type": "/some/path",
        "context": "not a dict",
    }
    assert convert(invalid_server_event) == []

    # Context missing path key
    invalid_server_event = {
        "event_source": "server",
        "event_type": "/some/path",
        "context": {"not_path": "/some/value"},
    }
    assert convert(invalid_server_event) == []
