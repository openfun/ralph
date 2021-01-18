"""Browser event xAPI Converter"""

import json

from ralph.schemas.edx.browser import (
    BaseBrowserEventSchema,
    BaseTextbookPdfBrowserEventSchema,
    PageCloseBrowserEventSchema,
    SeqGotoBrowserEventSchema,
    SeqNextBrowserEventSchema,
    SeqPrevBrowserEventSchema,
    TextbookPdfDisplayScaledBrowserEventSchema,
    TextbookPdfOutlineToggledBrowserEventSchema,
    TextbookPdfPageNavigatedBrowserEventSchema,
    TextbookPdfPageScrolledBrowserEventSchema,
    TextbookPdfThumbnailNavigatedBrowserEventSchema,
    TextbookPdfThumbnailsToggledBrowserEventSchema,
    TextbookPdfZoomButtonsChangedBrowserEventSchema,
    TextbookPdfZoomMenuChangedBrowserEventSchema,
)
from ralph.schemas.edx.converters.base import GetFromField

from .base import BaseXapiConverter
from .constants import (
    BOOK,
    INITIALIZED,
    INTERACTED,
    MODULE,
    PAGE,
    TERMINATED,
    XAPI_ACTIVITY_BOOK,
    XAPI_ACTIVITY_MODULE,
    XAPI_ACTIVITY_PAGE,
    XAPI_EXTENSION_COLLECTION_TYPE,
    XAPI_EXTENSION_DIRECTION,
    XAPI_EXTENSION_ENDING_POSITION,
    XAPI_EXTENSION_PATH,
    XAPI_EXTENSION_POSITION,
    XAPI_EXTENSION_SESSION,
    XAPI_EXTENSION_STARTING_POSITION,
    XAPI_EXTENSION_THUMBNAIL_TITLE,
    XAPI_EXTENSION_ZOOM_AMOUNT,
    XAPI_VERB_INITIALIZED,
    XAPI_VERB_INTERACTED,
    XAPI_VERB_TERMINATED,
)


class BaseBrowserEventToXapi(BaseXapiConverter):
    """Base class used by edX browser event converters to xAPI
    See BaseBrowserEventSchema for info about the edX browser event
    """

    _schema = BaseBrowserEventSchema()

    @property
    def context(self):
        context = super().context
        # All edX events have the path field equal to the url of the request.
        # But browser events are special!
        # The path field is always `/event` and the page field has the url.
        context["extensions"][XAPI_EXTENSION_PATH] = GetFromField("page")
        # Question: is it SAFE to have the md5 encrypted Django session keys (with salt)
        # in the xAPI statements ?
        context["extensions"][XAPI_EXTENSION_SESSION] = GetFromField("session")
        return context


class PageCloseBrowserEventToXapi(BaseBrowserEventToXapi):
    """Converts page_close browser edX event to xAPI
    Example Statement: John terminated https://www.fun-mooc.fr/ page
    """

    _schema = PageCloseBrowserEventSchema()

    @property
    def object(self):
        """Get statement object from event (required)"""
        return {
            "id": GetFromField("page"),
            "definition": {
                "type": XAPI_ACTIVITY_PAGE,
                "name": {"en": PAGE},
            },
            "objectType": "Activity",
        }

    @property
    def verb(self):
        """Get statement verb from event (required)"""
        return {"id": XAPI_VERB_TERMINATED, "display": {"en": TERMINATED}}


class SeqGotoBrowserEventToXapi(BaseBrowserEventToXapi):
    """Converts seq_goto browser edX event to xAPI
    Example Statement: John initialized module (sequential-block-id) activity
    at ending-position, previously initialized at starting-position
    """

    _schema = SeqGotoBrowserEventSchema()

    @property
    def context(self):
        context = super().context
        context["extensions"][XAPI_EXTENSION_ENDING_POSITION] = GetFromField(
            "event", lambda event: json.loads(event)["new"]
        )
        context["extensions"][XAPI_EXTENSION_STARTING_POSITION] = GetFromField(
            "event", lambda event: json.loads(event)["old"]
        )
        return context

    @property
    def object(self):
        """Get statement object from event (required)"""
        return {
            "id": GetFromField("event", lambda event: json.loads(event)["id"]),
            "definition": {
                "type": XAPI_ACTIVITY_MODULE,
                "name": {"en": MODULE},
                "extensions": {
                    XAPI_EXTENSION_COLLECTION_TYPE: GetFromField("event_type")
                },
            },
            "objectType": "Activity",
        }

    @property
    def verb(self):
        """Get statement verb from event (required)"""
        return {"id": XAPI_VERB_INITIALIZED, "display": {"en": INITIALIZED}}


class SeqNextBrowserEventToXapi(SeqGotoBrowserEventToXapi):
    """Converts seq_next browser edX event to xAPI
    See SeqGotoBrowserEventToXapi
    """

    _schema = SeqNextBrowserEventSchema()


class SeqPrevBrowserEventToXapi(SeqGotoBrowserEventToXapi):
    """Converts seq_prev browser edX event to xAPI
    See SeqGotoBrowserEventToXapi
    """

    _schema = SeqPrevBrowserEventSchema()


class BaseTextbookPdfBrowserEventToXapi(BaseBrowserEventToXapi):
    """Base class used by edX textbook browser event converters to xAPI.
    See BaseTextbookPdfBrowserEventSchema for info about the edX textbook browser event.
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.type-name"
    at position 1 (page of the book)
    """

    _schema = BaseTextbookPdfBrowserEventSchema()

    @property
    def context(self):
        context = super().context
        context["extensions"][XAPI_EXTENSION_POSITION] = GetFromField(
            "event", lambda event: json.loads(event)["page"]
        )
        return context

    @property
    def object(self):
        """Get statement object from event (required)"""
        return {
            "id": GetFromField("event", lambda event: json.loads(event)["chapter"]),
            "definition": {
                "type": XAPI_ACTIVITY_BOOK,
                "name": {"en": BOOK},
                "extensions": {
                    XAPI_EXTENSION_COLLECTION_TYPE: GetFromField("event_type")
                },
            },
            "objectType": "Activity",
        }

    @property
    def verb(self):
        """Get statement verb from event (required)"""
        return {"id": XAPI_VERB_INTERACTED, "display": {"en": INTERACTED}}


class TextbookPdfOutlineToggledBrowserEventToXapi(BaseTextbookPdfBrowserEventToXapi):
    """Converts textbook.pdf.outline.toggled browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.outline.toggled"
    at position 1 (page of the book)
    """

    _schema = TextbookPdfOutlineToggledBrowserEventSchema()


class TextbookPdfPageNavigatedBrowserEventToXapi(BaseTextbookPdfBrowserEventToXapi):
    """Converts textbook.pdf.page.navigated browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.page.navigated"
    at position 1 (page of the book)
    """

    _schema = TextbookPdfPageNavigatedBrowserEventSchema()


class TextbookPdfThumbnailsToggledBrowserEventToXapi(BaseTextbookPdfBrowserEventToXapi):
    """Converts textbook.pdf.thumbnails.toggled browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.thumbnails.toggled"
    at position 1 (page of the book)
    """

    _schema = TextbookPdfThumbnailsToggledBrowserEventSchema()


class TextbookPdfThumbnailNavigatedBrowserEventToXapi(
    BaseTextbookPdfBrowserEventToXapi
):
    """Converts textbook.pdf.thumbnail.navigated browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.thumbnail.navigated"
    having as thumbnail title "XYZ"
    at position 1 (page of the book)
    """

    _schema = TextbookPdfThumbnailNavigatedBrowserEventSchema()

    @property
    def object(self):
        object_property = super().object
        object_property["definition"]["extensions"][
            XAPI_EXTENSION_THUMBNAIL_TITLE
        ] = GetFromField("event", lambda event: json.loads(event)["thumbnail_title"])
        return object_property


class TextbookPdfZoomButtonsChangedBrowserEventToXapi(
    BaseTextbookPdfBrowserEventToXapi
):
    """Converts textbook.pdf.zoom.buttons.changed browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.zoom.buttons.changed"
    in the direction (in / out)
    at position 1 (page of the book)
    """

    _schema = TextbookPdfZoomButtonsChangedBrowserEventSchema()

    @property
    def object(self):
        object_property = super().object
        object_property["definition"]["extensions"][
            XAPI_EXTENSION_DIRECTION
        ] = GetFromField("event", lambda event: json.loads(event)["direction"])
        return object_property


class TextbookPdfPageScrolledBrowserEventToXapi(
    TextbookPdfZoomButtonsChangedBrowserEventToXapi
):
    """Converts textbook.pdf.page.scrolled browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.page.scrolled"
    in the direction (up / down)
    at position 1 (page of the book)
    """

    _schema = TextbookPdfPageScrolledBrowserEventSchema()


class TextbookPdfZoomMenuChangedBrowserEventToXapi(BaseTextbookPdfBrowserEventToXapi):
    """Converts textbook.pdf.zoom.menu.changed browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.zoom.menu.changed"
    of zoom amount ( 0.75 / 1.25 / 'page-actual' / 'auto' / etc. )
    at position 1 (page of the book)
    """

    _schema = TextbookPdfZoomMenuChangedBrowserEventSchema()

    @property
    def object(self):
        object_property = super().object
        object_property["definition"]["extensions"][
            XAPI_EXTENSION_ZOOM_AMOUNT
        ] = GetFromField("event", lambda event: json.loads(event)["amount"])
        return object_property


class TextbookPdfDisplayScaledBrowserEventToXapi(
    TextbookPdfZoomMenuChangedBrowserEventToXapi
):
    """Converts textbook.pdf.display.scaled browser edX event to xAPI
    Example Statement: John interacted with book-asset-path activity
    of (collection) type "textbook.pdf.display.scaled"
    of zoom amount ( 0.75 / 1.25 / other numerical values ... )
    at position 1 (page of the book)
    """

    _schema = TextbookPdfDisplayScaledBrowserEventSchema()
