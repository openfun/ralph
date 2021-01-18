"""
Browser event schema definitions
"""
import json
import urllib.parse

from marshmallow import ValidationError, validates, validates_schema
from marshmallow.fields import Field, Str, Url
from marshmallow.validate import URL, Equal, OneOf

from .base import BaseEventSchema

# pylint: disable=no-self-use, unused-argument

MD5_HASH_LEN = 32

BROWSER_EVENT_TYPE_FIELD = [
    "book",
    "page_close",
    "problem_check",
    "problem_graded",
    "problem_reset",
    "problem_save",
    "problem_show",
    "seq_goto",
    "seq_next",
    "seq_prev",
    "textbook.pdf.display.scaled",
    "textbook.pdf.outline.toggled",
    "textbook.pdf.page.navigated",
    "textbook.pdf.page.scrolled",
    "textbook.pdf.thumbnail.navigated",
    "textbook.pdf.thumbnails.toggled",
    "textbook.pdf.zoom.buttons.changed",
    "textbook.pdf.zoom.menu.changed",
]

BROWSER_NAME_FIELD = [
    "textbook.pdf.page.loaded",
    "textbook.pdf.page.navigatednext",
    "textbook.pdf.search.executed",
    "textbook.pdf.search.highlight.toggled",
    "textbook.pdf.search.navigatednext",
    "textbook.pdf.searchcasesensitivity.toggled",
]

BROWSER_EVENT_VALID_AMOUNT = [
    "0.5",
    "0.75",
    "1",
    "1.25",
    "1.5",
    "2",
    "3",
    "4",
    "auto",
    "page-actual",
    "page-fit",
    "page-width",
]


class BaseBrowserEventSchema(BaseEventSchema):
    """Represents common fields and functions all BrowserEvents inherit
    from. This type of event is triggered on (XHR) POST/GET request to
    the `/event` URL
    """

    event_source = Str(
        required=True,
        validate=Equal(
            comparable="browser", error="The event event_source field is not `browser`"
        ),
    )
    event_type = Str(
        required=True,
        validate=OneOf(
            choices=BROWSER_EVENT_TYPE_FIELD,
            error="The event name field value is not one of the valid values",
        ),
    )
    name = Str(required=True)
    page = Url(required=True, relative=True)
    session = Str(required=True)
    event = Field(required=True)

    @validates("session")
    def validate_session(self, value):
        """"Check session field empty or MD5_HASH_LEN chars long"""
        if value != "" and len(value) != MD5_HASH_LEN:
            raise ValidationError(
                f"Session should be empty or {MD5_HASH_LEN} chars long (MD5)"
            )

    @validates_schema
    def validate_name(self, data, **kwargs):
        """The name field should be equal to the event_type in case event_type
        is not `book`"""

        if data["event_type"] != "book" and data["event_type"] != data["name"]:
            raise ValidationError(
                "The name field should be equal to the event_type when event_type is not `book`"
            )
        if data["event_type"] == "book" and data["name"] not in BROWSER_NAME_FIELD:
            raise ValidationError("The name field is not one of the allowed values")

    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """Check that the context.path is equal to `/event`"""
        if data["context"]["path"] != "/event":
            raise ValidationError(
                f"Path should be `/event`, not `{data['context']['path']}`"
            )

    @staticmethod
    def validate_event_keys(data, required_keys):
        """Parse JSON string and check that it contains the keys in the
        `required_keys` set and no other keys
        """
        try:
            event = json.loads(data["event"])
        except (json.JSONDecodeError, TypeError) as err:
            raise ValidationError(
                "Event should contain a parsable JSON string"
            ) from err
        keys = set(event.keys())
        if keys != required_keys:
            raise ValidationError(
                f"{required_keys.difference(keys)} key is required for event, "
                f"{keys.difference(required_keys)} key is not valid for event"
            )
        return event

    @staticmethod
    def check_chapter_page_name(data, event):
        """Check that the `chapter` is an valid url
        the `name` should be equal to browser event field `name`
        and `page` should be an integer > 0
        """
        if not isinstance(event["page"], int) or not event["page"] > 0:
            raise ValidationError("Event page should a positive integer")

        if data["name"] != event["name"]:
            raise ValidationError(
                "Event name should be equal to the browser event name"
            )

        URL(relative=True)(event["chapter"])

        block_id = BaseEventSchema.get_block_id(
            data, prefix="/asset-v1", block_type="asset", suffix="/"
        )
        if event["chapter"][: len(block_id)] != block_id:
            raise ValidationError(
                f"Event chapter should begin with {block_id} , not "
                f"{event['chapter'][:len(block_id)]}"
            )
        if event["chapter"][-4:] != ".pdf":
            raise ValidationError("Event chapter should end with the .pdf extension")

    @staticmethod
    def check_name(data, name):
        """Check the name of the event is equal to the `name` argument"""
        if data["name"] != name:
            raise ValidationError(f"name field should be `{name}`")


class PageCloseBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when the JS event window.onunload is triggered"""

    @validates_schema
    def validate_event_page_close(self, data, **kwargs):
        """Check that event is empty dict when name is `page_close`"""
        self.check_name(data, "page_close")
        if data["event"] != "{}":
            raise ValidationError("Event should be an empty JSON")


class ProblemShowBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user clicks on the button `AFFICHER LA REPONSE`
    of a CAPA problem
    """

    @validates_schema
    def validate_event_problem_show(self, data, **kwargs):
        """Check that event is a parsable JSON object when name is `problem_show`"""
        self.check_name(data, "problem_show")
        if not data["context"]["org_id"]:
            raise ValidationError("Event context.org_id should not be empty")
        event = self.validate_event_keys(data, {"problem"})
        block_id = self.get_block_id(data)
        if event["problem"][:-MD5_HASH_LEN] != block_id:
            raise ValidationError(
                f"Event problem should start with `{block_id}`, not "
                f"{event['problem'][:-MD5_HASH_LEN]}"
            )


class ProblemCheckBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user submits a response to a CAPA problem"""

    @validates_schema
    def validate_event_problem_check(self, data, **kwargs):
        """Check that event is a standard URL-encoded string or empty"""
        self.check_name(data, "problem_check")
        if not data["event"]:
            return
        try:
            urllib.parse.parse_qs(data["event"], strict_parsing=True)
        except (ValueError, AttributeError) as exception:
            raise ValidationError(
                "Event should be a valid URL-encoded string"
            ) from exception


class BaseProblemBrowserEventSchema(BaseBrowserEventSchema):
    """Base class for problem_graded, problem_reset and problem_save
    Browser events
    """

    @validates_schema
    def validate_event_problem_graded_reset_save(self, data, **kwargs):
        """Check that event is a list of length 2 and that the first
        value is a valid URL-encoded string or empty
        """
        if not isinstance(data["event"], list) or len(data["event"]) != 2:
            raise ValidationError("Event should be a two-items list")

        if data["event"][0] == "":
            return

        try:
            urllib.parse.parse_qs(data["event"][0], strict_parsing=True)
        except (ValueError, AttributeError) as exception:
            raise ValidationError(
                "Event list first item should be a valid URL-encoded string"
            ) from exception


class ProblemGradedBrowserEventSchema(BaseProblemBrowserEventSchema):
    """Triggered when user submits a response to a CAPA problem"""

    @validates_schema
    def validate_event_problem_graded(self, data, **kwargs):
        """Check name is `problem_graded`"""
        self.check_name(data, "problem_graded")


class ProblemResetBrowserEventSchema(BaseProblemBrowserEventSchema):
    """Triggered when user clicks on the button `REINITIALISER`
    of a CAPA problem
    """

    @validates_schema
    def validate_event_problem_graded(self, data, **kwargs):
        """Check name is `problem_reset`"""
        self.check_name(data, "problem_reset")


class ProblemSaveBrowserEventSchema(BaseProblemBrowserEventSchema):
    """Triggered when user clicks on the button `ENREGISTRER`
    of an CAPA problem
    """

    @validates_schema
    def validate_event_problem_save(self, data, **kwargs):
        """Check name is `problem_save`"""
        self.check_name(data, "problem_save")


class SeqGotoBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user clicks on a sequence unit of the sequence
    navigation bar in a courseware page
    """

    @validates_schema
    def validate_event_seq_goto(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 3 keys:
        `new`: integer, `old`: integer, `id`: string
        Same validation applies to `seq_next`, `seq_prev` names
        """
        self.check_name(data, "seq_goto")
        event = self.validate_event_keys(data, {"new", "old", "id"})
        if not isinstance(event["new"], int) or not isinstance(event["old"], int):
            raise ValidationError("Event new and old fields should be integers")
        block_id = self.get_block_id(data, block_type="sequential")
        block_id_len = len(block_id)
        if event["id"][:block_id_len] != block_id:
            raise ValidationError(
                f"The id should start with {block_id} , not "
                f"{event['id'][:block_id_len]}"
            )
        if len(event["id"][block_id_len:]) != MD5_HASH_LEN:
            raise ValidationError(
                f"The id should end with a {MD5_HASH_LEN} long MD5 hash"
            )


class SeqNextBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user clicks on the right arrow of the sequence
    navigation bar
    """

    @validates_schema
    def validate_event_seq_next(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 3 keys:
        `new`: integer, `old`: integer, `id`: string
        and that `new` is equal to (`old` + 1)
        """
        self.check_name(data, "seq_next")
        event = self.validate_event_keys(data, {"new", "old", "id"})
        block_id = self.get_block_id(data, block_type="sequential")
        if event["id"][:-MD5_HASH_LEN] != block_id:
            raise ValidationError(
                f"the event.id value should start with {block_id} , not "
                f"{event['id'][:-MD5_HASH_LEN]}"
            )
        if event["old"] + 1 != event["new"]:
            raise ValidationError(
                f"Event new field ({event['new']}) should be equal to old ({event['old']}) + 1"
            )


class SeqPrevBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user clicks on the left arrow of the sequence
    navigation bar
    """

    @validates_schema
    def validate_event_seq_prev(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 3 keys:
        `new`: integer, `old`: integer, `id`: string
        and that `new` is equal to (`old` - 1)
        """
        self.check_name(data, "seq_prev")
        event = self.validate_event_keys(data, {"new", "old", "id"})
        block_id = self.get_block_id(data, block_type="sequential")
        if event["id"][:-MD5_HASH_LEN] != block_id:
            raise ValidationError(
                f"the event.id value should start with {block_id} , not "
                f"{event['id'][:-MD5_HASH_LEN]}"
            )
        if event["old"] - 1 != event["new"]:
            raise ValidationError(
                f"Event new field ({event['new']}) should be equal to old ({event['old']}) - 1"
            )


class BaseTextbookPdfBrowserEventSchema(BaseBrowserEventSchema):
    """Base class for textbook.pdf.outline.toggled
    textbook.pdf.page.navigated and textbook.pdf.thumbnails.toggled
    Browser events
    """

    @validates_schema
    def validate_event_textbook_pdf(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 3 keys:
        `name`: string, `page`: integer > 0, `chapter`: url
        and `name` should be equal to event `name`
        """
        event = self.validate_event_keys(data, {"chapter", "page", "name"})
        self.check_chapter_page_name(data, event)


class TextbookPdfOutlineToggledBrowserEventSchema(BaseTextbookPdfBrowserEventSchema):
    """Triggered when user clicks on the outline icon of the sidebar"""

    @validates_schema
    def validate_event_problem_save(self, data, **kwargs):
        """Check name is `textbook.pdf.outline.toggled`"""
        self.check_name(data, "textbook.pdf.outline.toggled")


class TextbookPdfPageNavigatedBrowserEventSchema(BaseTextbookPdfBrowserEventSchema):
    """Triggered when user manually enters a page number"""

    @validates_schema
    def validate_event_problem_save(self, data, **kwargs):
        """Check name is `textbook.pdf.page.navigated`"""
        self.check_name(data, "textbook.pdf.page.navigated")


class TextbookPdfThumbnailsToggledBrowserEventSchema(BaseTextbookPdfBrowserEventSchema):
    """Triggered when user clicks on the `Toggle sidebar` icon of the
    pdf iframe OR on the `Show thumbnails` icon of the sidebar
    """

    @validates_schema
    def validate_event_problem_save(self, data, **kwargs):
        """Check name is `textbook.pdf.thumbnails.toggled`"""
        self.check_name(data, "textbook.pdf.thumbnails.toggled")


class TextbookPdfThumbnailNavigatedBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user clicks on a thumbnail image to navigate
    to a page of the pdf
    """

    @validates_schema
    def validate_event_textbook_pdf_thumbnail_navigated(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
        `name`: string, `page`: integer > 0, `chapter`: url
        `thumbnail_title`: string
        """
        self.check_name(data, "textbook.pdf.thumbnail.navigated")

        event = self.validate_event_keys(
            data, {"chapter", "page", "name", "thumbnail_title"}
        )
        self.check_chapter_page_name(data, event)
        if not isinstance(event["thumbnail_title"], str):
            raise ValidationError("thumbnail_title should be a string")


class TextbookPdfZoomButtonsChangedBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user clicks on the Zoom In or Zoom Out icon"""

    @validates_schema
    def validate_event_textbook_pdf_zoom_buttons_changed(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
        `name`: string, `page`: integer > 0, `chapter`: url,
        `direction`: string (one of [`in`, `out`])
        """
        self.check_name(data, "textbook.pdf.zoom.buttons.changed")
        event = self.validate_event_keys(data, {"chapter", "page", "name", "direction"})
        self.check_chapter_page_name(data, event)
        valid_directions = ["in", "out"]
        if event["direction"] not in valid_directions:
            raise ValidationError(f"direction should be one of {valid_directions}")


class TextbookPdfPageScrolledBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user scrolls to the next or previous page using
    the mousewheel AND the `transition` takes less than 50 milliseconds
    """

    @validates_schema
    def validate_event_textbook_pdf_page_scrolled(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
        `name`: string, `page`: integer > 0, `chapter`: url,
        `direction`: string (one of [`up`, `down`])
        """
        self.check_name(data, "textbook.pdf.page.scrolled")
        event = self.validate_event_keys(data, {"chapter", "page", "name", "direction"})
        self.check_chapter_page_name(data, event)
        valid_directions = ["up", "down"]
        if event["direction"] not in valid_directions:
            raise ValidationError(f"direction should be one of {valid_directions}")


class TextbookPdfZoomMenuChangedBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when user selects a magnification setting"""

    @validates_schema
    def validate_event_textbook_pdf_zoom_menu_changed(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
        `name`: string, `page`: integer > 0, `chapter`: url,
        `amount`: string
        """
        self.check_name(data, "textbook.pdf.zoom.menu.changed")
        event = self.validate_event_keys(data, {"chapter", "page", "name", "amount"})
        self.check_chapter_page_name(data, event)
        if event["amount"] not in BROWSER_EVENT_VALID_AMOUNT:
            raise ValidationError(
                f"amount should be one of {BROWSER_EVENT_VALID_AMOUNT}"
            )


class TextbookPdfDisplayScaledBrowserEventSchema(BaseBrowserEventSchema):
    """Triggered when the first page is shown and when user selects a
    magnification setting OR zooms in/out the pdf iframe
    """

    @validates_schema
    def validate_event_textbook_pdf_display_scaled(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
        `name`: string, `page`: integer > 0, `chapter`: url,
        `amount`: float (integer)
        """
        self.check_name(data, "textbook.pdf.display.scaled")
        event = self.validate_event_keys(data, {"chapter", "page", "name", "amount"})
        self.check_chapter_page_name(data, event)
        if not isinstance(event["amount"], float):
            raise ValidationError("amount should be a float integer")
