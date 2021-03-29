"""Server event factory definitions"""

from factory import LazyAttribute

from ralph.models.edx.server import BaseServerEvent, ServerEvent

from .base import BaseEventFactory


class BaseServerEventFactory(BaseEventFactory):
    """Factory for the BaseServerEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseServerEvent

    event_source = "server"


class ServerEventFactory(BaseServerEventFactory):
    """Factory for the ServerEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = ServerEvent

    event_type = LazyAttribute(lambda self: self.context.path)
    event = '{"POST": {}, "GET": {}}'
