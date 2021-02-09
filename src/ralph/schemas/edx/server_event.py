"""Server event schema definitions"""

import json

from marshmallow import ValidationError, validates, validates_schema
from marshmallow.fields import Str, Url

from .base import BaseEventSchema

# pylint: disable=no-self-use, unused-argument


class ServerEventSchema(BaseEventSchema):
    """Represents a common server event.

    This type of event is triggered from the django middleware on each request excluding:
    `/event`, `login`, `heartbeat`, `/segmentio/event` and `/performance`.
    """

    event_type = Url(required=True, relative=True)
    """Consist of the relative URL (without the hostname) of the requested page.

    Retrieved with:
        `request.META['PATH_INFO']`
    Source:
        /common/djangoapps/track/views/__init__.py#L106
    """

    event = Str(required=True)
    """Consist of a JSON encoded string holding the content of the GET or POST request.

    Retrieved with:
        `json.dumps({'GET': dict(request.GET), 'POST': dict(request.POST)})[:512]`
    Note:
        Values for ['password', 'newpassword', 'new_password', 'oldpassword',
        'old_password', 'new_password1', 'new_password2'] are replaced by `********`.
        The JSON encoded string is truncated at 512 characters resulting in invalid JSON.
    Source:
        /common/djangoapps/track/middleware.py#L75
    """

    @validates_schema
    def validate_event_type(self, data, **kwargs):
        """The event_type should be equal to context.path"""

        if data["event_type"] != data["context"]["path"]:
            raise ValidationError("event_type should be equal to context.path")

    @validates("event")
    def validate_event(self, value):
        """Check that the event field contains a parsable JSON string with 2
        keys `POST` and `GET` and dictionaries as values. As the event field
        is truncated at 512 characters, it might be common that it would not be
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
