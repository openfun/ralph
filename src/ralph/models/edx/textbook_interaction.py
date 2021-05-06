"""Textbook interaction event model definitions"""

from typing import Literal, Optional, Union

from pydantic import Field, Json, constr

from ralph.models.selector import selector

from .base import AbstractBaseEventField
from .browser import BaseBrowserEvent


class TextbookInteractionBaseEventField(AbstractBaseEventField):
    """Represents the event field which attributes are common to most of the textbook
    interaction events.

    Attributes:
        chapter (str): Consists of the name of the PDF file.
            It begins with the `block_id` value and ends with the `.pdf` extension.
        page (int): The number of the page that is open when the event is emitted.
    """

    page: int
    chapter: constr(
        regex=(
            r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"  # noqa: F722
        )
    )


class TextbookPdfThumbnailsToggledEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.thumbnails.toggled` event field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.thumbnails.toggled`.
    """

    name: Literal["textbook.pdf.thumbnails.toggled"]


class TextbookPdfThumbnailNavigatedEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.thumbnail.navigated` event field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.thumbnail.navigated`.
    """

    name: Literal["textbook.pdf.thumbnail.navigated"]


class TextbookPdfOutlineToggledEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.outline.toggled` event field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.outline.toggled`.
    """

    name: Literal["textbook.pdf.outline.toggled"]


class TextbookPdfChapterNavigatedEventField(AbstractBaseEventField):
    """Represents the `textbook.pdf.chapter.navigated` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.chapter.navigated`.
        chapter (str): Consists of the name of the PDF file.
            It begins with the `block_id` value and ends with the `.pdf` extension.
    """

    name: Literal["textbook.pdf.chapter.navigated"]
    chapter: constr(
        regex=(
            r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"  # noqa: F722
        )
    )
    chapter_title: str


class TextbookPdfPageNavigatedEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.page.navigated` event field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.page.navigated`.
    """

    name: Literal["textbook.pdf.page.navigated"]


class TextbookPdfZoomButtonsChangedEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.zoom.buttons.changed` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.zoom.buttons.changed`.
        direction (str): Consists of either the `in` or `out` value.
    """

    name: Literal["textbook.pdf.zoom.buttons.changed"]
    direction: Union[Literal["in"], Literal["out"]]


class TextbookPdfZoomMenuChangedEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.zoom.menu.changed` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.zoom.menu.changed`.
        amount (str): Consists either of the `1`, `0.75`, `1.5`, `custom`,
            `page_actual`, `auto`, `page_width`, `page_fit` value.
    """

    name: Literal["textbook.pdf.zoom.menu.changed"]
    amount: Union[
        Literal["1"],
        Literal["0.5"],
        Literal["2"],
        Literal["3"],
        Literal["4"],
    ]


class TextbookPdfDisplayScaledEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.display.scaled` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.display.scaled`.
        amount (str): Consists of a floating point number string value.
    """

    name: Literal["textbook.pdf.display.scaled"]
    amount: float


class TextbookPdfPageScrolledEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.page.scrolled` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.page.scrolled`.
        direction (str): Consists either of the `up` or `down` value.
    """

    name: Literal["textbook.pdf.page.scrolled"]
    direction: Union[Literal["up"], Literal["down"]]


class TextbookPdfSearchExecutedEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.search.executed` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.search.executed`.
        caseSensitive (bool): Consists either of the `true` value if the case sensitive option
            is selected or `false` if this option is not selected.
        highlightAll (bool): Consists either of the `true` value if the option to highlight
            all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that is
            unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.search.executed"]
    caseSensitive: bool
    highlightAll: bool
    query: str
    status: str


class TextbookPdfSearchNavigatedNextEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.search.navigatednext` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.search.navigatednext`.
        caseSensitive (bool): Consists either of the `true` value if the case sensitive option
            is selected or `false` if this option is not selected.
        findPrevious(bool): Consists either of the ‘true’ value if the user clicks the
            Find Previous icon or ‘false’ if the user clicks the <kbd>Find Next</kbd> icon.
        highlightAll (bool): Consists either of the `true` value if the option to highlight
            all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that is
            unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.search.navigatednext"]
    caseSensitive: bool
    findPrevious: bool
    highlightAll: bool
    query: str
    status: str


class TextbookPdfSearchHighlightToggledEventField(TextbookInteractionBaseEventField):
    """Represents the `textbook.pdf.search.highlight.toggled` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.search.highlight.toggled`.
        caseSensitive (bool): Consists either of the `true` value if the case sensitive
            option is selected or `false` if this option is not selected.
        highlightAll (bool): Consists either of the `true` value if the option to highlight
            all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that is
            unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.search.highlight.toggled"]
    caseSensitive: bool
    highlightAll: bool
    query: str
    status: str


class TextbookPdfSearchCaseSensitivityToggledEventField(
    TextbookInteractionBaseEventField
):
    """Represents the `textbook.pdf.searchcasesensitivity.toggled` event field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.searchcasesensitivity.toggled`.
        caseSensitive (bool): Consists either of the `true` value if the case sensitive
            option is selected or `false` if this option is not selected.
        highlightAll (bool): Consists either of the `true` value if the option to highlight
            all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that is
            unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.searchcasesensitivity.toggled"]
    caseSensitive: bool
    highlightAll: bool
    query: str
    status: str


class BookEventField(AbstractBaseEventField):
    """Represents the `book` event field.

    Attributes:
        chapter (str): Consists of the name of the PDF file.
        name (str): Consists of `textbook.pdf.page.loaded` if type is set to `gotopage`,
            `textbook.pdf.page.navigatednext` if type is set to `prevpage`,
            `textbook.pdf.page.navigatednext` if type is set to `nextpage`.
        new (int): Consists of the destination page number.
        old (int): Consists of the original page number. It applies to `gotopage` event types only.
        type (str): Consists of `gotopage` value when a page loads after the student manually
            enters its number, `prevpage` value when the next page button is clicked or `nextpage`
            value when the previous page button is clicked.
    """

    chapter: constr(
        regex=(
            r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"  # noqa: F722
        )
    )
    name: Union[
        Literal["textbook.pdf.page.loaded"], Literal["textbook.pdf.page.navigatednext"]
    ]
    new: int
    old: Optional[int]
    type: Union[Literal["gotopage"], Literal["prevpage"], Literal["nextpage"]] = Field(
        alias="type"
    )


class UIBook(BaseBrowserEvent):
    """Represents the `book` browser event model.

    The browser emits this event when a user navigates within the PDF Viewer or the PNG Viewer.

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


class UITextbookPdfThumbnailsToggled(BaseBrowserEvent):
    """Represents the `textbook.pdf.thumbnails.toggled` browser event model.

    The browser emits this event when a user clicks on the icon to show or hide page thumbnails.

    Attributes:
        event (TextbookPdfThumbnailsToggledEventField):
            See TextbookPdfThumbnailsToggledEventField.
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


class UITextbookPdfThumbnailNavigated(BaseBrowserEvent):
    """Represents the `textbook.pdf.thumbnail.navigated` browser event model.

    The browser emits this event when a user clicks on a thumbnail image to navigate to a page.

    Attributes:
        event (TextbookPdfThumbnailNavigatedEventField):
            See TextbookPdfThumbnailNavigatedEventField.
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


class UITextbookPdfOutlineToggled(BaseBrowserEvent):
    """Represents the `textbook.pdf.outline.toggled` browser event model.

    The browser emits this event when a user clicks the outline icon to show or hide
    a list of the book’s chapters.

    Attributes:
        event (TextbookPdfOutlineToggledEventField):
            See TextbookPdfThumbnailNavigatedEventField.
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


class UITextbookPdfChapterNavigated(BaseBrowserEvent):
    """Represents the `textbook.pdf.chapter.navigated` browser event model.

    The browser emits this event when a user clicks on a link in the outline to navigate
    to a chapter.

    Attributes:
        event (TextbookPdfChapterNavigatedEventField):
            See TextbookPdfChapterNavigatedEventField.
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


class UITextbookPdfPageNavigated(BaseBrowserEvent):
    """Represents the `textbook.pdf.page.navigated` browser event model.

    The browser emits this event when a user manually enters a page number.

    Attributes:
        event (TextbookPdfPageNavigatedEventField): See TextbookPdfPageNavigatedEventField.
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


class UITextbookPdfZoomButtonsChanged(BaseBrowserEvent):
    """Represents the `textbook.pdf.zoom.buttons.changed` browser event model.

    The browser emits this event when a user clicks either the <kbd>Zoom In</kbd>
    or <kbd>Zoom Out</kbd> icon.

    Attributes:
        event (TextbookPdfZoomButtonsChangedEventField):
            See TextbookPdfZoomButtonsChangedEventField.
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


class UITextbookPdfZoomMenuChanged(BaseBrowserEvent):
    """Represents the `textbook.pdf.zoom.menu.changed` browser event model.

    The browser emits this event when a user selects a magnification setting.

    Attributes:
        event (TextbookPdfZoomMenuChangedEventField):
            See TextbookPdfZoomMenuChangedEventField.
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


class UITextbookPdfDisplayScaled(BaseBrowserEvent):
    """Represents the `textbook.pdf.display.scaled` browser event model.

    The browser emits this event when the display magnification changes or the first page
    is shown.

    Attributes:
        event (TextbookPdfDisplayScaledEventField): See TextbookPdfDisplayScaledEventField.
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


class UITextbookPdfPageScrolled(BaseBrowserEvent):
    """Represents the `textbook.pdf.page.scrolled` browser event model.

    The browser emits this event when the user scrolls to the next or previous page and
    the transition takes less than 50 milliseconds.

    Attributes:
        event (TextbookPdfPageScrolledEventField): See TextbookPdfPageScrolledEventField.
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


class UITextbookPdfSearchExecuted(BaseBrowserEvent):
    """Represents the `textbook.pdf.search.executed` browser event model.

    The browser emits this event when a user searches for a text value in the file.

    Attributes:
        event (TextbookPdfSearchExecutedEventField): See TextbookPdfSearchExecutedEventField.
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


class UITextbookPdfSearchNavigatedNext(BaseBrowserEvent):
    """Represents the `textbook.pdf.search.navigatednext` browser event model.

    The browser emits this event when a user clicks on the <kbd>Find Next</kbd> or
    <kbd>Find Previous</kbd> icons for an entered search string.

    Attributes:
        event (TextbookPdfSearchNavigatedNextEventField):
            See TextbookPdfSearchNavigatedNextEventField.
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


class UITextbookPdfSearchHighlightToggled(BaseBrowserEvent):
    """Represents the `textbook.pdf.search.highlight.toggled` browser event model.

    The browser emits this event when a user searches for a text value in the file.

    Attributes:
        event (TextbookPdfSearchHighlightToggledEventField):
            See TextbookPdfSearchHighlightToggledEventField.
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


class UITextbookPdfSearchCaseSensitivityToggled(BaseBrowserEvent):
    """Represents the `textbook.pdf.searchcasesensitivity.toggled` browser event model.

    The browser emits this event when a user searches for a text value in the file.

    Attributes:
        event (TextbookPdfSearchCaseSensitivityToggledEventField):
            See TextbookPdfSearchCaseSensitivityToggledEventField.
        event_type (str): Consists of the value `textbook.pdf.searchcasesensitivity.toggled`.
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
