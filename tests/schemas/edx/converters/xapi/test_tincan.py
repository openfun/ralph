"""Test that all defined edX to xAPI converters produce valid xAPI statements using TinCanPython"""

import copy
import json
from io import StringIO

import pytest
from tincan import Statement

from ralph.schemas.edx.converters.xapi_converter_selector import (
    Converters,
    XapiConverterSelector,
)

from tests.fixtures.logs import EventType, event_generator

PLATFORM = "https://fun-mooc.fr"
EVENT_COUNT = 200
CONVERTER_EVENTS = [(Converters.SERVER, event_generator(EventType.SERVER, EVENT_COUNT))]
CONVERTER_EVENTS = [(x[0], x) for x in CONVERTER_EVENTS]
CONVERTER_STATEMENTS = {}


@pytest.fixture
def statements(request):
    """Prepare CONVERTOR_STATEMENTS for parametrized tests"""

    converter = request.param[0]
    events = request.param[1]
    if converter in CONVERTER_STATEMENTS:
        return CONVERTER_STATEMENTS[converter]

    with StringIO() as file:
        # Write events to file
        for event in events:
            file.write(json.dumps(event) + "\n")
        file.seek(0)
        # Convert, deserialize and store events from file in converted_events list
        converter_selector = XapiConverterSelector(PLATFORM)
        CONVERTER_STATEMENTS[converter] = []
        for converted_event in converter_selector.convert(file):
            assert converted_event is not None
            CONVERTER_STATEMENTS[converter].append(json.loads(converted_event))
    return CONVERTER_STATEMENTS[converter]


def test_each_converter_should_have_corresponding_events():
    """This test ensure that EVENTS is in sync with Converters enum.
    For each event, the CONVERTER._select_converter method should returns the
    corresponding converter.
    """

    converter_event_dict = {}
    for converter, converter_events in CONVERTER_EVENTS:
        converter_event_dict[converter] = converter_events[1]
    for converter in Converters:
        assert converter in converter_event_dict
        assert len(converter_event_dict[converter]) == EVENT_COUNT
        for event in converter_event_dict[converter]:
            converter_selector = XapiConverterSelector(PLATFORM)
            converter_selector.event = event
            # pylint: disable=protected-access
            assert isinstance(converter_selector._select_converter(), converter.value)


@pytest.mark.parametrize(
    "converter,statements", CONVERTER_EVENTS, indirect=["statements"]
)
def test_xapi_statements_should_be_valid(
    converter, statements
):  # pylint: disable=unused-argument,redefined-outer-name
    """Let TinCanPython validate that the converted events are valid"""

    for statement in statements:
        tincan_statement = json.loads(Statement(copy.deepcopy(statement)).to_json())
        assert statement == tincan_statement
