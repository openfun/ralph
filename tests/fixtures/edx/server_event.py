"""Server event factory definitions"""

import factory
from faker import Faker

from ralph.schemas.edx.server_event import ServerEventSchema

from .base import BaseEventFactory

FAKE = Faker()
Faker.seed(1)

# pylint: disable=no-self-argument, no-self-use, no-member, unsubscriptable-object


class ServerEventFactory(BaseEventFactory):
    """Represents a common server event factory
    This type of event is triggered on each request excluding:
    `/event`, `login`, `heartbeat`, `/segmentio/event`, `/performance`
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = ServerEventSchema

    @factory.lazy_attribute
    def event_type(self):
        """Return the event_type which is equal to the path"""

        return self.context["path"]

    @factory.sequence
    def event(number):
        """Return a randomly empty/filled POST/GET value"""

        empty = '{"POST": {}, "GET": {}}'
        post = (
            '{"POST": {"input_e8bc718966e9441abc3ccf1a6429ee8b_2_1": ["choice_2"]},'
            ' "GET": {}}'
        )
        get = '{"POST": {}, "GET": {"rpp": ["50"], "page": ["1"]}}'
        return FAKE.random_element([empty, post, get])
