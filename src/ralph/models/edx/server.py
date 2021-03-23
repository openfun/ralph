"""Server event model definitions"""

import json
from pathlib import Path
from typing import Literal

from pydantic import root_validator, validator

from ralph.models.selector import LazyModelField, selector

from .base import BaseEventModel


class BaseServerEventModel(BaseEventModel):
    """Represents the base server event model all server events inherit from."""

    event_source: Literal["server"]


class ServerEventModel(BaseServerEventModel):
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

    __selector__ = selector(
        event_source="server", event_type=LazyModelField("context__path")
    )

    # pylint: disable=unsubscriptable-object
    event_type: Path
    event: str

    @validator("event")
    def validate_event(cls, event_str):  # pylint: disable=no-self-argument, no-self-use
        """Checks that the `event` field is a JSON string object containing GET and POST keys."""

        try:
            event = json.loads(event_str)
        except (json.JSONDecodeError, TypeError) as err:
            raise ValueError("must be a JSON string") from err
        keys = {"POST", "GET"}
        for key in keys:
            if not isinstance(event.get(key, None), dict):
                raise ValueError(
                    f"{key} field should exist and its value must be a dictionary"
                )
        if not set(event.keys()) == keys:
            raise ValueError("extra fields not permitted")
        return event_str

    @root_validator
    def validate_event_type(
        cls, values
    ):  # pylint: disable=no-self-argument, no-self-use
        """Check that the event_type and context.path values are equal."""

        if values.get("event_type") != values.get("context").path:
            raise ValueError("event_type should be equal to context.path")
        return values
