"""Server event model definitions."""

import sys
from pathlib import Path
from typing import Union

from pydantic import Json

from ralph.models.selector import LazyModelField, selector

from .base import AbstractBaseEventField, BaseEdxModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class BaseServerModel(BaseEdxModel):
    """Pydantic model for core server statement."""

    event_source: Literal["server"]


class ServerEventField(AbstractBaseEventField):
    """Pydantic model for common server `event` field."""

    GET: dict
    POST: dict


class Server(BaseServerModel):
    """Pydantic model for common server statement.

    This type of event is triggered from the django middleware on each request
    excluding: `/event`, `login`, `heartbeat`, `/segmentio/event` and `/performance`.

    Attributes:
        event_type (str): Consist of the relative URL (without the hostname) of the
            requested page.
            Retrieved with:
                `request.META['PATH_INFO']`
        event (str): Consist of a JSON string holding the content of the GET or POST
            request.
            Retrieved with:
                ```json.dumps(
                    {
                        'GET': dict(request.GET),
                        'POST': dict(request.POST)
                    }
                )[:512]```
            Note:
                Values for ['password', 'newpassword', 'new_password', 'oldpassword',
                'old_password', 'new_password1', 'new_password2'] are replaced by
                `********`.
                The JSON string is truncated at 512 characters resulting in invalid
                JSON.
    """

    __selector__ = selector(
        event_source="server", event_type=LazyModelField("context__path")
    )

    # pylint: disable=unsubscriptable-object
    event_type: Path
    event: Union[Json[ServerEventField], ServerEventField]
