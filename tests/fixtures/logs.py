"""Logs format pytest fixtures"""

import logging
from enum import Enum
from secrets import token_hex
from tempfile import NamedTemporaryFile

import pytest
from logging_gelf.formatters import GELFFormatter

from .edx.base import BaseEventFactory
from .edx.browser import (
    BaseBrowserEventFactory,
    PageCloseBrowserEventFactory,
    ProblemCheckBrowserEventFactory,
    ProblemGradedBrowserEventFactory,
    ProblemResetBrowserEventFactory,
    ProblemSaveBrowserEventFactory,
    ProblemShowBrowserEventFactory,
    SeqGotoBrowserEventFactory,
    SeqNextBrowserEventFactory,
    SeqPrevBrowserEventFactory,
    TextbookPdfDisplayScaledBrowserEventFactory,
    TextbookPdfOutlineToggledBrowserEventFactory,
    TextbookPdfPageNavigatedBrowserEventFactory,
    TextbookPdfPageScrolledBrowserEventFactory,
    TextbookPdfThumbnailNavigatedBrowserEventFactory,
    TextbookPdfThumbnailsToggledBrowserEventFactory,
    TextbookPdfZoomButtonsChangedBrowserEventFactory,
    TextbookPdfZoomMenuChangedBrowserEventFactory,
)
from .edx.feedback_displayed import FeedbackDisplayedFactory
from .edx.ora.base_ora_event import BaseOraEventFactory
from .edx.ora.create_submission import CreateSubmissionFactory
from .edx.ora.save_submission import SaveSubmissionFactory
from .edx.server_event import ServerEventFactory


class EventType(Enum):
    """Represents a list of defined Event Types"""

    BASE_EVENT = BaseEventFactory
    BASE_ORA_EVENT = BaseOraEventFactory
    BROWSER_BASE = BaseBrowserEventFactory
    BROWSER_PAGE_CLOSE = PageCloseBrowserEventFactory
    BROWSER_PROBLEM_CHECK = ProblemCheckBrowserEventFactory
    BROWSER_PROBLEM_GRADED = ProblemGradedBrowserEventFactory
    BROWSER_PROBLEM_RESET = ProblemResetBrowserEventFactory
    BROWSER_PROBLEM_SAVE = ProblemSaveBrowserEventFactory
    BROWSER_PROBLEM_SHOW = ProblemShowBrowserEventFactory
    BROWSER_SEQ_GOTO = SeqGotoBrowserEventFactory
    BROWSER_SEQ_NEXT = SeqNextBrowserEventFactory
    BROWSER_SEQ_PREV = SeqPrevBrowserEventFactory
    BROWSER_TEXTBOOK_PDF_DISPLAY_SCALED = TextbookPdfDisplayScaledBrowserEventFactory
    BROWSER_TEXTBOOK_PDF_OUTLINE_TOGGLED = TextbookPdfOutlineToggledBrowserEventFactory
    BROWSER_TEXTBOOK_PDF_PAGE_NAVIGATED = TextbookPdfPageNavigatedBrowserEventFactory
    BROWSER_TEXTBOOK_PDF_PAGE_SCROLLED = TextbookPdfPageScrolledBrowserEventFactory
    BROWSER_TEXTBOOK_PDF_THUMBNAIL_NAVIGATED = (
        TextbookPdfThumbnailNavigatedBrowserEventFactory
    )
    BROWSER_TEXTBOOK_PDF_THUMBNAILS_TOGGLED = (
        TextbookPdfThumbnailsToggledBrowserEventFactory
    )
    BROWSER_TEXTBOOK_PDF_ZOOM_BUTTONS_CHANGED = (
        TextbookPdfZoomButtonsChangedBrowserEventFactory
    )
    BROWSER_TEXTBOOK_PDF_ZOOM_MENU_CHANGED = (
        TextbookPdfZoomMenuChangedBrowserEventFactory
    )
    CREATE_SUBMISSION = CreateSubmissionFactory
    FEEDBACK_DISPLAYED = FeedbackDisplayedFactory
    SAVE_SUBMISSION = SaveSubmissionFactory
    SERVER = ServerEventFactory


def event_generator(event_type_enum, size=1, **kwargs):
    """Generate `size` number of events of type `event_type_enum`

    Args:
        event_type (EventType): The type of event to be generated.
        size (integer): Number of events to be generated
        kwargs: Declarations to use for the generated factory

    Returns:
        A dict representing the event when size is 1
        A size long list of events when size is more than 1

    """

    if size == 1:
        return event_type_enum.value.create(**kwargs)
    return event_type_enum.value.create_batch(size, **kwargs)


@pytest.fixture
def event():
    """Returns an event generator that generates size number of events
    of the given event_type.
    """

    return event_generator


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
