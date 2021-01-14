"""
base event factory for ora (openassessment) events
"""
import factory
from faker import Faker

from ralph.schemas.edx.ora.base_ora_event import BaseOraEventSchema

from ..base import BaseEventFactory, ContextFactory

FAKE = Faker()


class BaseOraEventFactory(BaseEventFactory):
    """Represents the base event factory for ora events"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = BaseOraEventSchema

    username = factory.Sequence(lambda n: FAKE.profile().get("username"))
    page = "x_module"
    context = factory.LazyAttribute(lambda o: ContextFactory(**o.context_args))
