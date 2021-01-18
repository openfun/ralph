"""Entrypoint to convert events to xAPI"""

import json
import logging
from enum import Enum

from .xapi.browser_event_to_xapi import (
    PageCloseBrowserEventToXapi,
    SeqGotoBrowserEventToXapi,
    SeqNextBrowserEventToXapi,
    SeqPrevBrowserEventToXapi,
    TextbookPdfDisplayScaledBrowserEventToXapi,
    TextbookPdfOutlineToggledBrowserEventToXapi,
    TextbookPdfPageNavigatedBrowserEventToXapi,
    TextbookPdfPageScrolledBrowserEventToXapi,
    TextbookPdfThumbnailNavigatedBrowserEventToXapi,
    TextbookPdfThumbnailsToggledBrowserEventToXapi,
    TextbookPdfZoomButtonsChangedBrowserEventToXapi,
    TextbookPdfZoomMenuChangedBrowserEventToXapi,
)
from .xapi.server_event_to_xapi import ServerEventToXapi

# converters module logger
logger = logging.getLogger(__name__)

# These Browser events are less specific duplicates of server events.
# We choose to not convert them.
IGNORED_BROWSER_EVENTS = (
    "problem_check",  # server problem_check
    "problem_graded",  # server problem_check
    "problem_reset",  # server reset_problem
    "problem_save",  # server save_problem_success / save_problem_fail
    "problem_show",  # server showanswer
)


class Converters(Enum):
    """Stores initialized xAPI converters"""

    SERVER = ServerEventToXapi
    BROWSER_PAGE_CLOSE = PageCloseBrowserEventToXapi
    BROWSER_SEQ_GOTO = SeqGotoBrowserEventToXapi
    BROWSER_SEQ_NEXT = SeqNextBrowserEventToXapi
    BROWSER_SEQ_PREV = SeqPrevBrowserEventToXapi
    BROWSER_TEXTBOOK_PDF_DISPLAY_SCALED = TextbookPdfDisplayScaledBrowserEventToXapi
    BROWSER_TEXTBOOK_PDF_OUTLINE_TOGGLED = TextbookPdfOutlineToggledBrowserEventToXapi
    BROWSER_TEXTBOOK_PDF_PAGE_NAVIGATED = TextbookPdfPageNavigatedBrowserEventToXapi
    BROWSER_TEXTBOOK_PDF_PAGE_SCROLLED = TextbookPdfPageScrolledBrowserEventToXapi
    BROWSER_TEXTBOOK_PDF_THUMBNAIL_NAVIGATED = (
        TextbookPdfThumbnailNavigatedBrowserEventToXapi
    )
    BROWSER_TEXTBOOK_PDF_THUMBNAILS_TOGGLED = (
        TextbookPdfThumbnailsToggledBrowserEventToXapi
    )
    BROWSER_TEXTBOOK_PDF_ZOOM_BUTTONS_CHANGED = (
        TextbookPdfZoomButtonsChangedBrowserEventToXapi
    )
    BROWSER_TEXTBOOK_PDF_ZOOM_MENU_CHANGED = (
        TextbookPdfZoomMenuChangedBrowserEventToXapi
    )


BROWSER_EVENT_TYPE_TO_CONVERTER = {
    "page_close": Converters.BROWSER_PAGE_CLOSE,
    "seq_goto": Converters.BROWSER_SEQ_GOTO,
    "seq_next": Converters.BROWSER_SEQ_NEXT,
    "seq_prev": Converters.BROWSER_SEQ_PREV,
    "textbook.pdf.display.scaled": Converters.BROWSER_TEXTBOOK_PDF_DISPLAY_SCALED,
    "textbook.pdf.outline.toggled": Converters.BROWSER_TEXTBOOK_PDF_OUTLINE_TOGGLED,
    "textbook.pdf.page.navigated": Converters.BROWSER_TEXTBOOK_PDF_PAGE_NAVIGATED,
    "textbook.pdf.page.scrolled": Converters.BROWSER_TEXTBOOK_PDF_PAGE_SCROLLED,
    "textbook.pdf.thumbnail.navigated": Converters.BROWSER_TEXTBOOK_PDF_THUMBNAIL_NAVIGATED,
    "textbook.pdf.thumbnails.toggled": Converters.BROWSER_TEXTBOOK_PDF_THUMBNAILS_TOGGLED,
    "textbook.pdf.zoom.buttons.changed": Converters.BROWSER_TEXTBOOK_PDF_ZOOM_BUTTONS_CHANGED,
    "textbook.pdf.zoom.menu.changed": Converters.BROWSER_TEXTBOOK_PDF_ZOOM_MENU_CHANGED,
}


class XapiConverterSelector:
    """Select a matching xAPI converter to convert to xAPI format"""

    def __init__(self, platform):
        """Initialise XapiConverterSelector

        Args:
            platform (str): URL of the platform to which the event belongs

        """

        self.event = None
        self.converters = {
            converter: converter.value(platform) for converter in Converters
        }

    def convert(self, input_file):
        """Uses a matching xAPI converter to validate and return the converted event"""

        for event in input_file:
            try:
                self.event = json.loads(event)
            except (json.JSONDecodeError, TypeError):
                self._log_error("Invalid event! Not parsable JSON!")
                continue
            if not isinstance(self.event, dict):
                self._log_error("Invalid event! Not a dictionary!")
                continue
            converter = self._select_converter()
            if not converter:
                continue
            yield converter.convert(self.event)

    def _select_converter(self):
        """Return a xAPI converter that matches the event"""

        event_source = self.event.get("event_source", None)
        if not event_source:
            self._log_error("Invalid event! Missing event_source!")
            return None
        if event_source == "server":
            return self._select_server_converter()
        if event_source == "browser":
            return self._select_browser_converter()
        self._log_error("No matching xAPI converter found!")
        return None

    def _select_server_converter(self):
        """Return a xAPI server converter that matches the event"""

        event_type = self.event.get("event_type", None)
        context = self.event.get("context", None)
        if not event_type or not context:
            self._log_error("Invalid event! Missing event_type or context!")
            return None
        if not isinstance(context, dict):
            self._log_error("Invalid event! Context not a dictionary!")
            return None
        if event_type == context.get("path", None):
            return self.converters[Converters.SERVER]
        self._log_error("No matching server xAPI converter found!")
        return None

    def _select_browser_converter(self):
        """Return a xAPI browser converter that matches the event"""

        event_type = self.event.get("event_type", None)
        if not event_type:
            self._log_error("Invalid event! Missing event_type!")
            return None
        converter_type = BROWSER_EVENT_TYPE_TO_CONVERTER.get(event_type, None)
        if converter_type:
            return self.converters[converter_type]
        if event_type in IGNORED_BROWSER_EVENTS:
            return None
        self._log_error("No matching browser xAPI converter found!")
        return None

    def _log_error(self, message):
        logger.error(message)
        logger.debug("For Event : %s", self.event)
