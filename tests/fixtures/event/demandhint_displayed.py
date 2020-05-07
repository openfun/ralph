"""
edx.problem.hint.demandhint_displayed event fixture definition
"""

from faker import Faker

from .base import BaseEvent, FreeEventField, TiedEventField
from .server import BaseServerEvent, BaseTriggeredEvent

# Faker.seed(0)
FAKE = Faker()


class DemandHintDisplayedEventField(BaseEvent):
    """Represents the event field of an
    edx.problem.hint.demandhint_displayed event
    """

    def __init__(self, *args, **kwargs):
        super(DemandHintDisplayedEventField, self).__init__(*args, **kwargs)
        hint_len = FAKE.random_int(0, 10)
        self.hint_index = FAKE.random_int(0, hint_len)
        self.module_id = TiedEventField(
            BaseServerEvent.get_module_id, dependency="context"
        )
        self.hint_len = hint_len
        self.hint_text = FreeEventField(FAKE.sentence, emptiable_str=True)


class DemandHintDisplayedEvent(BaseTriggeredEvent):
    """Represents the edx.problem.hint.demandhint_displayed event
    This type of event is triggered when the user click on a
    hint button of a CAPA problem
    """

    def __init__(self, *args, **kwargs):
        super(DemandHintDisplayedEvent, self).__init__(*args, **kwargs)
        self.context.path = self.context.path + "/hint_button"
        self.event = DemandHintDisplayedEventField(*args, **kwargs.get("event", {}))
