"""
Server event factory definitions
"""
import factory
from faker import Faker

from ralph.schemas.edx.server import ServerEventSchema

from .base import _BaseEventFactory
from .mixins import JSONFactoryMixin, ObjFactoryMixin

FAKE = Faker()


class _ServerEventFactory(_BaseEventFactory):
    """Represents a common server event factory
    This type of event is triggered on each request excluding:
    `/event`, `login`, `heartbeat`, `/segmentio/event`, `/performance`
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = ServerEventSchema

    # pylint: disable=no-member, unsubscriptable-object
    @factory.lazy_attribute
    def event_type(self):
        """Returns the event_type which is equal to the path"""
        return self.context["path"]

    # pylint: disable=no-self-argument, no-self-use
    @factory.sequence
    def event(number):
        """ returns randomly empty/filled POST/GET value"""
        empty = '{"POST": {}, "GET": {}}'
        post = (
            '{"POST": {"input_e8bc718966e9441abc3ccf1a6429ee8b_2_1": ["choice_2"]},'
            ' "GET": {}}'
        )
        get = '{"POST": {}, "GET": {"rpp": ["50"], "page": ["1"]}}'
        return FAKE.random_element([empty, post, get])


class ServerEventStrFactory(JSONFactoryMixin, _ServerEventFactory):
    """ Creates JSON Serialized model of the factory data """


class ServerEventObjFactory(ObjFactoryMixin, _ServerEventFactory):
    """ Creates Deserialized model of the factory data """
