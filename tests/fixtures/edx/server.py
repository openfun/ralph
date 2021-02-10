"""Server event factory definitions"""

from factory import LazyAttribute

from ralph.models.edx.server import ServerEventModel

from .base import BaseEventFactory


class ServerEventFactory(BaseEventFactory):
    """Factory for the ServerEventModel"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = ServerEventModel

    event_type = LazyAttribute(lambda self: self.context.path)
    event = '{"POST": {}, "GET": {}}'
