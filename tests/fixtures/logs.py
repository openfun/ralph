"""
Logs format pytest fixtures.
"""
import logging
from enum import Enum, auto
from secrets import token_hex
from tempfile import NamedTemporaryFile

import pandas as pd
import pytest
from djehouty.libgelf.formatters import GELFFormatter

from .event.base import BaseEventObjFactory
from .event.feedback_displayed import FeedbackDisplayedObjFactory
from .event.server import ServerEventObjFactory


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


class EventType(Enum):
    """Represents a list of defined Event Types"""

    BASEEVENT = auto()
    SERVER = auto()
    FEEDBACK_DISPLAYED = auto()


EVENT_TYPES = {
    EventType.BASEEVENT.value: BaseEventObjFactory,
    EventType.FEEDBACK_DISPLAYED.value: FeedbackDisplayedObjFactory,
    EventType.SERVER.value: ServerEventObjFactory,
}


def _event(size, event_type_enum, **kwargs):
    """Generate `size` number of events of type `event_type`

    Args:
        size (integer): Number of events to be generated
        event_type (EventType): The type of event to be generated.
        kwargs: Declarations to use for the generated factory

    Returns:
        DataFrame: With one event per row and size number of rows
    """
    return pd.DataFrame(
        EVENT_TYPES.get(event_type_enum.value).create_batch(size, **kwargs)
    )


@pytest.fixture
def event():
    """Returns an event generator that generates size number of events
    of the given event_type.
    """
    return _event
