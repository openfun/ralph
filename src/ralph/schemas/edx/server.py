"""
Server event schema definitions
"""
import json

from marshmallow import ValidationError, validates, validates_schema
from marshmallow.fields import Str, Url

from .base import BaseEventSchema

# pylint: disable=no-self-use, unused-argument


class ServerEventSchema(BaseEventSchema):
    """Represents a common server event.
    This type of event is triggered on each request excluding:
    `/event`, `login`, `heartbeat`, `/segmentio/event`, `/performance`
    """

    event_type = Url(required=True, relative=True)
    event = Str(required=True)

    @validates_schema
    def validate_event_type(self, data, **kwargs):
        """the event_type should be equal to context.path"""
        if data["event_type"] != data["context"]["path"]:
            raise ValidationError("event_type should be equal to context.path")

    @validates("event")
    def validate_event(self, value):
        """check that the event field contains a parsable json string with 2
        keys `POST` and `GET` and dictionaries as values. As the event field
        is truncated at 500 characters, it might be common that it would not be
        parsable.
        """
        try:
            event = json.loads(value)
        except json.JSONDecodeError as err:
            raise ValidationError("Server event should contain a JSON string") from err

        if len(event) != 2:
            raise ValidationError("Server event field should exactly have two keys")

        if "POST" not in event or "GET" not in event:
            raise ValidationError("Server event should contain GET and POST keys")

        if not isinstance(event["POST"], dict) or not isinstance(event["GET"], dict):
            raise ValidationError(
                "Server event GET and POST values should be serialized objects"
            )
