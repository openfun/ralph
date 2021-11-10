"""Textbook interaction event model definitions"""

from typing import Literal, Union

from pydantic import Json

from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from .fields.events import (
    BookEventField,
    TextbookPdfChapterNavigatedEventField,
    TextbookPdfDisplayScaledEventField,
    TextbookPdfOutlineToggledEventField,
    TextbookPdfPageNavigatedEventField,
    TextbookPdfPageScrolledEventField,
    TextbookPdfSearchCaseSensitivityToggledEventField,
    TextbookPdfSearchExecutedEventField,
    TextbookPdfSearchHighlightToggledEventField,
    TextbookPdfSearchNavigatedNextEventField,
    TextbookPdfThumbnailNavigatedEventField,
    TextbookPdfThumbnailsToggledEventField,
    TextbookPdfZoomButtonsChangedEventField,
    TextbookPdfZoomMenuChangedEventField,
)


class UIBook(BaseBrowserModel):
    """Represents the `book` browser event model.

    The browser emits this event when a user navigates within the PDF Viewer or the
    PNG Viewer.

    Attributes:
        event (BookEventField): See BookEventField.
        event_type (str): Consists of the value `book`.
        name (str): Consists of the value `book`.
    """

    __selector__ = selector(event_source="browser", event_type="book")

    event: Union[
        Json[BookEventField], BookEventField  # pylint: disable=unsubscriptable-object
    ]
    event_type: Literal["book"]
    name: Literal["book"]


class UITextbookPdfThumbnailsToggled(BaseBrowserModel):
    """Represents the `textbook.pdf.thumbnails.toggled` browser event model.

    The browser emits this event when a user clicks on the icon to show or hide page
    thumbnails.

    Attributes:
        event (json): See TextbookPdfThumbnailsToggledEventField.
        event_type (str): Consists of the value `textbook.pdf.thumbnails.toggled`.
        name (str): Consists of the value `textbook.pdf.thumbnails.toggled`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.thumbnails.toggled"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfThumbnailsToggledEventField
        ],
        TextbookPdfThumbnailsToggledEventField,
    ]
    event_type: Literal["textbook.pdf.thumbnails.toggled"]
    name: Literal["textbook.pdf.thumbnails.toggled"]


class UITextbookPdfThumbnailNavigated(BaseBrowserModel):
    """Represents the `textbook.pdf.thumbnail.navigated` browser event model.

    The browser emits this event when a user clicks on a thumbnail image to navigate
    to a page.

    Attributes:
        event (json): See TextbookPdfThumbnailNavigatedEventField.
        event_type (str): Consists of the value `textbook.pdf.thumbnail.navigated`.
        name (str): Consists of the value `textbook.pdf.thumbnail.navigated`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.thumbnail.navigated"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfThumbnailNavigatedEventField
        ],
        TextbookPdfThumbnailNavigatedEventField,
    ]
    event_type: Literal["textbook.pdf.thumbnail.navigated"]
    name: Literal["textbook.pdf.thumbnail.navigated"]


class UITextbookPdfOutlineToggled(BaseBrowserModel):
    """Represents the `textbook.pdf.outline.toggled` browser event model.

    The browser emits this event when a user clicks the outline icon to show or hide
    a list of the book’s chapters.

    Attributes:
        event (json): See TextbookPdfOutlineToggledEventField.
        event_type (str): Consists of the value `textbook.pdf.outline.toggled`.
        name (str): Consists of the value `textbook.pdf.outline.toggled`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.outline.toggled"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfOutlineToggledEventField
        ],
        TextbookPdfOutlineToggledEventField,
    ]
    event_type: Literal["textbook.pdf.outline.toggled"]
    name: Literal["textbook.pdf.outline.toggled"]


class UITextbookPdfChapterNavigated(BaseBrowserModel):
    """Represents the `textbook.pdf.chapter.navigated` browser event model.

    The browser emits this event when a user clicks on a link in the outline to navigate
    to a chapter.

    Attributes:
        event (json): See TextbookPdfChapterNavigatedEventField.
        event_type (str): Consists of the value `textbook.pdf.chapter.navigated`.
        name (str): Consists of the value `textbook.pdf.chapter.navigated`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.chapter.navigated"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfChapterNavigatedEventField
        ],
        TextbookPdfChapterNavigatedEventField,
    ]
    event_type: Literal["textbook.pdf.chapter.navigated"]
    name: Literal["textbook.pdf.chapter.navigated"]


class UITextbookPdfPageNavigated(BaseBrowserModel):
    """Represents the `textbook.pdf.page.navigated` browser event model.

    The browser emits this event when a user manually enters a page number.

    Attributes:
        event (json): See TextbookPdfPageNavigatedEventField.
        event_type (str): Consists of the value `textbook.pdf.page.navigated`.
        name (str): Consists of the value `textbook.pdf.page.navigated`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.page.navigated"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfPageNavigatedEventField
        ],
        TextbookPdfPageNavigatedEventField,
    ]
    event_type: Literal["textbook.pdf.page.navigated"]
    name: Literal["textbook.pdf.page.navigated"]


class UITextbookPdfZoomButtonsChanged(BaseBrowserModel):
    """Represents the `textbook.pdf.zoom.buttons.changed` browser event model.

    The browser emits this event when a user clicks either the <kbd>Zoom In</kbd>
    or <kbd>Zoom Out</kbd> icon.

    Attributes:
        event (json): See TextbookPdfZoomButtonsChangedEventField.
        event_type (str): Consists of the value `textbook.pdf.zoom.buttons.changed`.
        name (str): Consists of the value `textbook.pdf.zoom.buttons.changed`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.zoom.buttons.changed"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfZoomButtonsChangedEventField
        ],
        TextbookPdfZoomButtonsChangedEventField,
    ]
    event_type: Literal["textbook.pdf.zoom.buttons.changed"]
    name: Literal["textbook.pdf.zoom.buttons.changed"]


class UITextbookPdfZoomMenuChanged(BaseBrowserModel):
    """Represents the `textbook.pdf.zoom.menu.changed` browser event model.

    The browser emits this event when a user selects a magnification setting.

    Attributes:
        event (json): See TextbookPdfZoomMenuChangedEventField.
        event_type (str): Consists of the value `textbook.pdf.zoom.menu.changed`.
        name (str): Consists of the value `textbook.pdf.zoom.menu.changed`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.zoom.menu.changed"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfZoomMenuChangedEventField
        ],
        TextbookPdfZoomMenuChangedEventField,
    ]
    event_type: Literal["textbook.pdf.zoom.menu.changed"]
    name: Literal["textbook.pdf.zoom.menu.changed"]


class UITextbookPdfDisplayScaled(BaseBrowserModel):
    """Represents the `textbook.pdf.display.scaled` browser event model.

    The browser emits this event when the display magnification changes or the first
    page is shown.

    Attributes:
        event (json): See TextbookPdfDisplayScaledEventField.
        event_type (str): Consists of the value `textbook.pdf.display.scaled`.
        name (str): Consists of the value `textbook.pdf.display.scaled`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.display.scaled"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfDisplayScaledEventField
        ],
        TextbookPdfDisplayScaledEventField,
    ]
    event_type: Literal["textbook.pdf.display.scaled"]
    name: Literal["textbook.pdf.display.scaled"]


class UITextbookPdfPageScrolled(BaseBrowserModel):
    """Represents the `textbook.pdf.page.scrolled` browser event model.

    The browser emits this event when the user scrolls to the next or previous page and
    the transition takes less than 50 milliseconds.

    Attributes:
        event (json): See TextbookPdfPageScrolledEventField.
        event_type (str): Consists of the value `textbook.pdf.page.scrolled`.
        name (str): Consists of the value `textbook.pdf.page.scrolled`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.page.scrolled"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfPageScrolledEventField
        ],
        TextbookPdfPageScrolledEventField,
    ]
    event_type: Literal["textbook.pdf.page.scrolled"]
    name: Literal["textbook.pdf.page.scrolled"]


class UITextbookPdfSearchExecuted(BaseBrowserModel):
    """Represents the `textbook.pdf.search.executed` browser event model.

    The browser emits this event when a user searches for a text value in the file.

    Attributes:
        event (json): See TextbookPdfSearchExecutedEventField.
        event_type (str): Consists of the value `textbook.pdf.search.executed`.
        name (str): Consists of the value `textbook.pdf.search.executed`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.search.executed"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfSearchExecutedEventField
        ],
        TextbookPdfSearchExecutedEventField,
    ]
    event_type: Literal["textbook.pdf.search.executed"]
    name: Literal["textbook.pdf.search.executed"]


class UITextbookPdfSearchNavigatedNext(BaseBrowserModel):
    """Represents the `textbook.pdf.search.navigatednext` browser event model.

    The browser emits this event when a user clicks on the <kbd>Find Next</kbd> or
    <kbd>Find Previous</kbd> icons for an entered search string.

    Attributes:
        event (json): See TextbookPdfSearchNavigatedNextEventField.
        event_type (str): Consists of the value `textbook.pdf.search.navigatednext`.
        name (str): Consists of the value `textbook.pdf.search.navigatednext`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.search.navigatednext"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfSearchNavigatedNextEventField
        ],
        TextbookPdfSearchNavigatedNextEventField,
    ]
    event_type: Literal["textbook.pdf.search.navigatednext"]
    name: Literal["textbook.pdf.search.navigatednext"]


class UITextbookPdfSearchHighlightToggled(BaseBrowserModel):
    """Represents the `textbook.pdf.search.highlight.toggled` browser event model.

    The browser emits this event when a user selects or clears the
    <kbd>Highlight All</kbd> option.

    Attributes:
        event (json): See TextbookPdfSearchHighlightToggledEventField.
        event_type (str): Consists of the value `textbook.pdf.search.highlight.toggled`.
        name (str): Consists of the value `textbook.pdf.search.highlight.toggled`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.search.highlight.toggled"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfSearchHighlightToggledEventField
        ],
        TextbookPdfSearchHighlightToggledEventField,
    ]
    event_type: Literal["textbook.pdf.search.highlight.toggled"]
    name: Literal["textbook.pdf.search.highlight.toggled"]


class UITextbookPdfSearchCaseSensitivityToggled(BaseBrowserModel):
    """Represents the `textbook.pdf.searchcasesensitivity.toggled` browser event model.

    The browser emits this event when a user selects or clears the
    <kbd>Match Case</kbd> option.

    Attributes:
        event (json): See TextbookPdfSearchCaseSensitivityToggledEventField.
        event_type (str): Consists of the value
            `textbook.pdf.searchcasesensitivity.toggled`.
        name (str): Consists of the value `textbook.pdf.searchcasesensitivity.toggled`.
    """

    __selector__ = selector(
        event_source="browser", event_type="textbook.pdf.searchcasesensitivity.toggled"
    )

    event: Union[
        Json[  # pylint: disable=unsubscriptable-object
            TextbookPdfSearchCaseSensitivityToggledEventField
        ],
        TextbookPdfSearchCaseSensitivityToggledEventField,
    ]
    event_type: Literal["textbook.pdf.searchcasesensitivity.toggled"]
    name: Literal["textbook.pdf.searchcasesensitivity.toggled"]
