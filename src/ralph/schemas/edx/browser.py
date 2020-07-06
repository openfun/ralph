"""
Browser event schema definitions
"""
import json
import urllib.parse

from marshmallow import ValidationError, fields, validates, validates_schema
from marshmallow.validate import URL, Equal, OneOf

from .base import BaseEventSchema

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


class BrowserEventSchema(BaseEventSchema):
    """Represents a common browser event.
    This type of event is triggered on (XHR) POST/GET request to the
    `/event` URL
    """

    event_source = fields.Str(
        required=True,
        validate=Equal(
            comparable="browser", error='The event event_source field is not "browser"'
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

    # pylint: disable=no-self-use
    @validates_schema
    def validate_name(self, data, **kwargs):
        """The name field should be equal to the event_type in case event_type
        is not `book` """

        if data["event_type"] != "book" and data["event_type"] != data["name"]:
            raise ValidationError(
                "the name field should be equal to the event_type when event_type is not `book`"
            )
        if data["event_type"] == "book" and data["name"] not in BROWSER_NAME_FIELD:
            raise ValidationError("the name field is not one of the allowed values")

    # pylint: disable=no-self-use
    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """Check that the context.path is equal to `/event`"""
        if data["context"]["path"] != "/event":
            raise ValidationError(
                f"Path should be `/event`, not `{data['context']['path']}`"
            )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_page_close(self, data, **kwargs):
        """Check that event is empty dict when name is `page_close`"""
        if data["name"] == "page_close":
            if data["event"] != "{}":
                raise ValidationError("Event should be empty when name is `page_close`")

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_problem_show(self, data, **kwargs):
        """Check that event is a parsable JSON object when name is `problem_show`"""
        if data["name"] != "problem_show":
            return

        if data["context"]["org_id"] == "":
            raise ValidationError(
                "Event context.org_id should not be empty for problem_show browser events"
            )
        try:
            event = json.loads(data["event"])
        except (json.JSONDecodeError, TypeError):
            raise ValidationError("Event should contain a parsable JSON string")

        if len(event) != 1 or "problem" not in event:
            raise ValidationError("Event should contain a `problem` key")

        # FIXME implement a course key getter from a context course id
        course_key = data["context"]["course_id"][10:]
        # FIXME do not hard-code problem key parsing size
        if event["problem"][:-32] != f"block-v1:{course_key}+type@problem+block@":
            raise ValidationError(
                f"Event problem should start with `block-v1:{course_key}+type@problem+block`"
            )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_problem_check(self, data, **kwargs):
        """Check that event is a standard URL-encoded string or empty"""
        if data["name"] != "problem_check" or data["event"] == "":
            return

        try:
            urllib.parse.parse_qs(data["event"], strict_parsing=True)
        except (ValueError, AttributeError):
            raise ValidationError("Event should be a valid URL-encoded string")

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_problem_graded_reset_save(self, data, **kwargs):
        """check that event is a list of lenght 2 and that the first
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

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_seq_goto(self, data, **kwargs):
        """check that the event is a string containing a json object
        with 3 keys: `new`: integer, `old`: integer, `id`: string
        Same validation applies to `seq_next`, `seq_prev` names
        """
        if data["name"] not in ["seq_goto", "seq_next", "seq_prev"]:
            return

        try:
            event = json.loads(data["event"])
        except (json.JSONDecodeError, TypeError):
            raise ValidationError("Event should contain a parsable JSON string")

        required_keys = {"new", "old", "id"}
        keys = set(event.keys())
        if len(required_keys.intersection(keys)) != 3:
            raise ValidationError(
                f"{required_keys.difference(keys)} key is required for event"
            )

        if not isinstance(event["new"], int) or not isinstance(event["old"], int):
            raise ValidationError("Event new and old fields should be integer")

        # FIXME course key parser
        course_key = data["context"]["course_id"][10:]
        if event["id"][:-32] != f"block-v1:{course_key}+type@sequential+block@":
            raise ValidationError(
                f"the event.id value should start with "
                f"block-v1:{course_key}+type@problem+block"
            )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_seq_next_seq_prev(self, data, **kwargs):
        """check that the event is a string containing a json object
        with 3 keys: `new`: integer, `old`: integer, `id`: string
        and that `new` is equal to (`old` + 1) for seq_next
        (and the opposite) for seq_prev
        """
        if data["name"] not in ("seq_next", "seq_prev"):
            return

        diff = 1 if data["name"] == "seq_next" else -1

        try:
            event = json.loads(data["event"])
        except (json.JSONDecodeError, TypeError):
            raise ValidationError("Event should contain a parsable json string")

        if event["old"] + diff != event["new"]:
            raise ValidationError(
                f"Event new ({event['new']}) should be equal to old "
                f"({event['old']}) + diff ({diff})"
            )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_textbook_pdf(self, data, **kwargs):
        """check that the event is a string containing a json object
        with 3 keys: `name`: string, `page`: integer > 0, `chapter`: url
        and `name` should be equal to event `name`
        """
        if data["name"] not in (
            "textbook.pdf.outline.toggled",
            "textbook.pdf.page.navigated",
            "textbook.pdf.thumbnails.toggled",
        ):
            return

        try:
            event = json.loads(data["event"])
        except (json.JSONDecodeError, TypeError):
            raise ValidationError("Event should contain a parsable json string")

        required_keys = {"name", "page", "chapter"}
        keys = set(event.keys())
        if len(required_keys.intersection(keys)) != 3:
            raise ValidationError(
                f"{required_keys.difference(keys)} key is required for event"
            )

        if not isinstance(event["page"], int) or not event["page"] > 0:
            raise ValidationError("Event page should a positive integer")

        if data["name"] != event["name"]:
            raise ValidationError(
                "Event name should be equal to the browser event name"
            )

        URL(relative=True)(event["chapter"])

        # FIXME course-key parser
        course_key = data["context"]["course_id"][10:]
        chapter_begin = f"/asset-v1:{course_key}+type@asset+block/"
        if event["chapter"][: len(chapter_begin)] != chapter_begin:
            raise ValidationError(f"Event chapter should begin with {chapter_begin}")
        if event["chapter"][-4:] != ".pdf":
            raise ValidationError("Event chapter should end with the .pdf extension")

    # pylint: no-self-use
    @validates("session")
    def validate_session(self, value):
        """"check session field empty or 32 chars long"""
        if value != "" and len(value) != 32:
            raise ValidationError("Session should be empty or 32 chars long (md5 key)")
