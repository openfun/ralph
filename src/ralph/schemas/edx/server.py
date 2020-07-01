"""
Server event schema definitions
"""
import json

from marshmallow import ValidationError, fields, validates_schema

from .base import BaseEventSchema


class ServerEventSchema(BaseEventSchema):
    """Represents a common server event.
    This type of event is triggered on each request excluding:
    `/event`, `login`, `heartbeat`, `/segmentio/event`, `/performance`
    """

    # pylint: disable=no-self-use
    @validates_schema
    def validate_event_type(self, data, **kwargs):
        """the event_type should be equal to context.path"""
        if data["event_type"] != data["context"]["path"]:
            raise ValidationError("event_type should be equal to context.path")

    # pylint: disable=no-self-argument, no-self-use
    def validate_event(value):
        """check that the event field contains a parsable json string
        with 2 keys `POST` and `GET` and dictionaries as values.
        As the event field is trunkated at 500 characters, it might be
        common that it would not be parsable.
        """
        try:
            event = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("event field should contain a parsable json string")
        keys = list(event.keys())
        if len(keys) != 2:
            raise ValidationError("event field parsed json should have 2 keys")
        if "POST" not in keys or "GET" not in keys:
            raise ValidationError(
                "event field parsed json should contain GET and POST keys"
            )
        if not isinstance(event["POST"], dict) or not isinstance(event["GET"], dict):
            raise ValidationError(
                "event.get and event.post values should be dictionaries"
            )

    event_type = fields.Url(required=True, relative=True)
    event = fields.Str(required=True, validate=validate_event)
