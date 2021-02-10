"""Server event model definitions"""

from pathlib import Path

from pydantic import Json, root_validator

from .base import BaseEventModel, BaseModelWithConfig


class ServerEventField(BaseModelWithConfig):
    """Represents the `event` field of the ServerEventModel"""

    GET: dict
    POST: dict


class ServerEventModel(BaseEventModel):
    """Represents a common server event.

    This type of event is triggered from the django middleware on each request excluding:
    `/event`, `login`, `heartbeat`, `/segmentio/event` and `/performance`.

    Attributes:
        event_type (str): Consist of the relative URL (without the hostname) of the requested page.
            Retrieved with:
                `request.META['PATH_INFO']`
        event (str): Consist of a JSON string holding the content of the GET or POST request.
            Retrieved with:
                `json.dumps({'GET': dict(request.GET), 'POST': dict(request.POST)})[:512]`
            Note:
                Values for ['password', 'newpassword', 'new_password', 'oldpassword',
                'old_password', 'new_password1', 'new_password2'] are replaced by `********`.
                The JSON string is truncated at 512 characters resulting in invalid JSON.
    """

    event_type: Path
    event: Json[ServerEventField]  # pylint: disable=unsubscriptable-object

    @root_validator
    def validate_event_type(
        cls, values
    ):  # pylint: disable=no-self-argument, no-self-use
        """Check that the event_type and context.path values are equal"""

        if values.get("event_type") != values.get("context").path:
            raise ValueError("event_type should be equal to context.path")
        return values
