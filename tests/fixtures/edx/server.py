"""Server event factory definitions"""

from factory import LazyAttribute

from ralph.models.edx.server import BaseServerEventModel, ServerEventModel

from .base import BaseEventFactory


class BaseServerEventFactory(BaseEventFactory):
    """Factory for the BaseServerEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseServerEventModel

    event_source = "server"


class ServerEventFactory(BaseServerEventFactory):
    """Factory for the ServerEventModel."""

    class Meta:  # pylint: disable=missing-class-docstring
        model = ServerEventModel

    event_type = LazyAttribute(lambda self: self.context.path)
    event = '{"POST": {}, "GET": {}}'
