"""
Browser event schema definitions
"""
import json
import urllib.parse

from marshmallow import ValidationError, fields, validates, validates_schema
from marshmallow.validate import URL, Equal, OneOf

from .base import BaseEventSchema

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

BROWSER_EVENT_VALID_AMAUNT = [
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


class BrowserEventSchema(BaseEventSchema):
    """Represents a common browser event.
    This type of event is triggered on (XHR) POST/GET request to the
    `/event` URL
    """

    event_source = fields.Str(
        required=True,
        validate=Equal(
            comparable="browser", error="The event event_source field is not `browser`"
        ),
    )
    event_type = fields.Str(
        required=True,
        validate=OneOf(
            choices=BROWSER_EVENT_TYPE_FIELD,
            error="The event name field value is not one of the valid values",
        ),
    )
    name = fields.Str(required=True)
    page = fields.Url(required=True, relative=True)
    session = fields.Str(required=True)
    event = fields.Field(required=True)

    # pylint: disable=no-self-use, unused-argument

    @validates_schema
    def validate_name(self, data, **kwargs):
        """The name field should be equal to the event_type in case event_type
        is not `book` """

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

    @validates_schema
    def validate_event_page_close(self, data, **kwargs):
        """Check that event is empty dict when name is `page_close`"""
        if data["name"] == "page_close" and data["event"] != "{}":
            raise ValidationError(
                "Event should be an empty JSON when name is `page_close`"
            )

    @validates_schema
    def validate_event_problem_show(self, data, **kwargs):
        """Check that event is a parsable JSON object when name is `problem_show`"""
        if data["name"] != "problem_show":
            return

        if data["context"]["org_id"] == "":
            raise ValidationError(
                "Event context.org_id should not be empty for problem_show browser events"
            )
        event = self.validate_event_keys(data, {"problem"})
        block_id = self.get_block_id(data)
        if event["problem"][:-MD5_HASH_LEN] != block_id:
            raise ValidationError(
                f"Event problem should start with `{block_id}`, not "
                f"{event['problem'][:-MD5_HASH_LEN]}"
            )

    @validates_schema
    def validate_event_problem_check(self, data, **kwargs):
        """Check that event is a standard URL-encoded string or empty"""
        if data["name"] != "problem_check" or data["event"] == "":
            return

        try:
            urllib.parse.parse_qs(data["event"], strict_parsing=True)
        except (ValueError, AttributeError):
            raise ValidationError("Event should be a valid URL-encoded string")

    @validates_schema
    def validate_event_problem_graded_reset_save(self, data, **kwargs):
        """Check that event is a list of lenght 2 and that the first
        value is a valid URL-encoded string or empty
        for event_types `problem_graded`, `problem_reset` and `problem_save`
        """
        if data["name"] not in ("problem_graded", "problem_reset", "problem_save"):
            return

        if not isinstance(data["event"], list) or len(data["event"]) != 2:
            raise ValidationError("Event should be a two-items list")

        if data["event"][0] == "":
            return

        try:
            urllib.parse.parse_qs(data["event"][0], strict_parsing=True)
        except (ValueError, AttributeError):
            raise ValidationError(
                "Event list first item should be a valid URL-encoded string"
            )

    @validates_schema
    def validate_event_seq_goto(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 3 keys:
        `new`: integer, `old`: integer, `id`: string
        Same validation applies to `seq_next`, `seq_prev` names
        """
        if data["name"] not in ["seq_goto"]:
            return

        event = self.validate_event_keys(data, {"new", "old", "id"})
        if not isinstance(event["new"], int) or not isinstance(event["old"], int):
            raise ValidationError("Event new and old fields should be integer")

        block_id = self.get_block_id(data, block_type="sequential")
        block_id_len = len(block_id)
        if event["id"][:block_id_len] != block_id:
            raise ValidationError(
                f"The id should start with {block_id} , not "
                f"{event['id'][:block_id_len]}"
            )
        if len(event["id"][block_id_len:]) != 32:
            raise ValidationError(
                f"The id should end with a {MD5_HASH_LEN} long MD5 hash"
            )

    @validates_schema
    def validate_event_seq_next_seq_prev(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 3 keys:
        `new`: integer, `old`: integer, `id`: string
        and that `new` is equal to (`old` + 1) for seq_next
        (and the opposite) for seq_prev
        """
        if data["name"] not in ("seq_next", "seq_prev"):
            return

        diff = 1 if data["name"] == "seq_next" else -1
        event = self.validate_event_keys(data, {"new", "old", "id"})
        block_id = self.get_block_id(data, block_type="sequential")
        if event["id"][:-MD5_HASH_LEN] != block_id:
            raise ValidationError(
                f"the event.id value should start with {block_id} , not "
                f"{event['id'][:-MD5_HASH_LEN]}"
            )
        if event["old"] + diff != event["new"]:
            raise ValidationError(
                f"Event new ({event['new']}) should be equal to old "
                f"({event['old']}) + diff ({diff})"
            )

    @validates_schema
    def validate_event_textbook_pdf(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 3 keys:
        `name`: string, `page`: integer > 0, `chapter`: url
        and `name` should be equal to event `name`
        """
        if data["name"] not in (
            "textbook.pdf.outline.toggled",
            "textbook.pdf.page.navigated",
            "textbook.pdf.thumbnails.toggled",
        ):
            return

        event = self.validate_event_keys(data, {"chapter", "page", "name"})
        self.check_chapter_page_name(data, event)

    @validates_schema
    def validate_event_textbook_pdf_thumbnail_navigated(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
         `name`: string, `page`: integer > 0, `chapter`: url
         `thumbnail_title`: string """
        if data["name"] != "textbook.pdf.thumbnail.navigated":
            return

        event = self.validate_event_keys(
            data, {"chapter", "page", "name", "thumbnail_title"}
        )
        self.check_chapter_page_name(data, event)
        if not isinstance(event["thumbnail_title"], str):
            raise ValidationError("thumbnail_title should be a string")

    @validates_schema
    def validate_event_textbook_pdf_zoom_buttons_changed(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
        `name`: string, `page`: integer > 0, `chapter`: url,
        `direction`: string (one of [`in`, `out`] or [`up`, `down`])
        """
        if data["name"] not in [
            "textbook.pdf.zoom.buttons.changed",
            "textbook.pdf.page.scrolled",
        ]:
            return

        event = self.validate_event_keys(data, {"chapter", "page", "name", "direction"})
        self.check_chapter_page_name(data, event)
        valid_directions = (
            ["in", "out"] if data["name"][-7:] == "changed" else ["up", "down"]
        )
        if event["direction"] not in valid_directions:
            raise ValidationError(f"direction should be one of {valid_directions}")

    @validates_schema
    def validate_event_textbook_pdf_zoom_menu_changed(self, data, **kwargs):
        """Check that the event is a parsable JSON object with 4 keys:
        `name`: string, `page`: integer > 0, `chapter`: url,
        `amaunt`: string
        """
        if data["name"] != "textbook.pdf.zoom.menu.changed":
            return

        event = self.validate_event_keys(data, {"chapter", "page", "name", "amaunt"})
        self.check_chapter_page_name(data, event)
        if event["amaunt"] not in BROWSER_EVENT_VALID_AMAUNT:
            raise ValidationError(
                f"amaunt should be one of {BROWSER_EVENT_VALID_AMAUNT}"
            )

    @validates("session")
    def validate_session(self, value):  # pylint: no-self-use
        """"Check session field empty or MD5_HASH_LEN chars long"""
        if value != "" and len(value) != MD5_HASH_LEN:
            raise ValidationError(
                f"Session should be empty or {MD5_HASH_LEN} chars long (MD5)"
            )

    @staticmethod
    def validate_event_keys(data, required_keys):
        """Parse JSON string and check that it contains the keys in the
        `required_keys` set and no other keys
        """
        try:
            event = json.loads(data["event"])
        except (json.JSONDecodeError, TypeError):
            raise ValidationError("Event should contain a parsable JSON string")
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
        and `page` should be an integer > 0"""
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
