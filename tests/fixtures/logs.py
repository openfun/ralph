"""
Logs format pytest fixtures.
"""
import logging
from enum import Enum
from secrets import token_hex
from tempfile import NamedTemporaryFile

import pandas as pd
import pytest
from djehouty.libgelf.formatters import GELFFormatter
from faker import Faker

from .event.browser import BrowserEvent
from .event.demandhint_displayed import DemandHintDisplayedEvent
from .event.feedback_displayed import FeedbackDisplayedEvent
from .event.problem_check import ProblemCheckEvent
from .event.server import BaseServerEvent

# Faker.seed(0)
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


class EventType(Enum):
    """Represents a list of defined Event Types for now"""

    SERVER = "server"
    BROWSER = "browser"
    DEMANDHINT_DISPLAYED = "demandhint_displayed"
    FEEDBACK_DISPLAYED = "feedback_displayed"
    PROBLEM_CHECK = "problem_check"


EVENT_TYPES = {
    EventType.SERVER.value: {
        "obj": BaseServerEvent,
        "sub_type": [""],
        "default_sub_type": "",
        "traits": {"is_anonymous": [True, False]},
    },
    EventType.BROWSER.value: {
        "obj": BrowserEvent,
        "sub_type": [
            "page_close",
            "problem_show",
            "problem_check",
            "problem_graded",
            "problem_reset",
            "problem_save",
            "seq_goto",
            "seq_next",
            "seq_prev",
            "textbook.pdf.thumbnails.toggled",
            "textbook.pdf.thumbnail.navigated",
            "textbook.pdf.outline.toggled",
            "textbook.pdf.zoom.buttons.changed",
            "textbook.pdf.zoom.menu.changed",
            "textbook.pdf.page.scrolled",
            "textbook.pdf.page.navigated",
            "textbook.pdf.display.scaled",
            "book",
        ],
        "default_sub_type": "page_close",
        "traits": {
            "is_anonymous": [True, False],
            "book_event_type": [
                "textbook.pdf.page.loaded",
                "textbook.pdf.page.navigatednext",
                "textbook.pdf.search.executed",
                "textbook.pdf.search.highlight.toggled",
                "textbook.pdf.search.navigatednext",
                "textbook.pdf.searchcasesensitivity.toggled",  # not a typo
            ],
        },
    },
    EventType.DEMANDHINT_DISPLAYED.value: {
        "obj": DemandHintDisplayedEvent,
        "sub_type": [],
        "default_sub_type": "edx.problem.hint.demandhint_displayed",
        "traits": {},
    },
    EventType.FEEDBACK_DISPLAYED.value: {
        "obj": FeedbackDisplayedEvent,
        "sub_type": [],
        "default_sub_type": "edx.problem.hint.feedback_displayed",
        "traits": {},
    },
    EventType.PROBLEM_CHECK.value: {
        "obj": ProblemCheckEvent,
        "sub_type": [],
        "default_sub_type": "problem_check",
        "traits": {
            "event": {
                "set_randomization_seed": ["NEVER", "PER_STUDENT", "OTHER"],
                "set_nb_of_questions": "any_number",
                "set_nb_of_answers": "any_number",
                "set_answer_types": [
                    "EMPTY",
                    "MULTIPLE_CHOICE",
                    "NUMERICAL_INPUT",
                    "DROP_DOWN",
                    "CHECKBOXES",
                    # or a lambda function without arguments
                ],
            }
        },
    },
}


EVENT_ARGS = [
    "set_all_null",  # sets all fields to empty/None if possible
    "set_all_filled",  # all fields that can be filled will be filled
    "remove_optional",  # removes all optional fields
    "keep_optional",  # keeps all optional fields
]


@pytest.fixture
def event():
    """Returns an event generator that generates size number of events
    of the given event_type and sub_type.
    Values from EVENT_ARGS can be passed as *args to alter the
    default behaviour.
    Values from EVENT_TYPES.*.traits can be passed as **kwargs to
    specify additional cases.
    Event fields can be overriden by passing event_field_name=value
    as **kwargs
    """

    def _event(size, event_type, *args, **kwargs):
        """Returns `size` number of events of type `event_type`

        Args:
            size (integer): specifies the number of events to be returned
            event_type (EventType or string): specifies the type of event
                to be generated. If event_type is a string it should be
                one of the values of the EventType enum
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value
        selected_event_type = EVENT_TYPES.get(event_type, EVENT_TYPES["server"])
        sub_type = kwargs.pop("sub_type", "")
        if sub_type in selected_event_type["sub_type"]:
            selected_sub_type = sub_type
        else:
            selected_sub_type = selected_event_type["default_sub_type"]
        selected_args = []
        for arg in args:
            if arg in EVENT_ARGS:
                selected_args.append(arg)

        result = []
        for _ in range(size):
            generator = selected_event_type["obj"](
                *selected_args, sub_type=selected_sub_type, **kwargs
            )
            result.append(generator.get())
        return pd.DataFrame(result)

    return _event
