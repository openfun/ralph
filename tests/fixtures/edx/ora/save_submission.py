"""
openassessmentblock.save_submission event factory definition
"""
import json

import factory
from faker import Faker

from ralph.schemas.edx.ora.save_submission import (
    SaveSubmissionEventSchema,
    SaveSubmissionSchema,
)

from ..base import BaseFactory, ContextFactory
from .base_ora_event import BaseOraEventFactory

# pylint: disable=no-member, no-self-argument, no-self-use

FAKE = Faker()


class SaveSubmissionEventFactory(BaseFactory):
    """Represents the Event Field factory of an
    openassessmentblock.save_submission
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = SaveSubmissionEventSchema

    @factory.sequence
    def saved_response(number):
        """ returns the saved_response field"""
        parts_value = []
        for _ in range(FAKE.random_digit_not_null()):
            parts_value.append({"text": FAKE.sentence()})
        saved_response = {"parts": parts_value}
        return json.dumps(saved_response)


class SaveSubmissionFactory(BaseOraEventFactory):
    """Represents the openassessmentblock.save_submission event factory"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = SaveSubmissionSchema

    event_type = "openassessmentblock.save_submission"
    event = factory.Sequence(lambda n: SaveSubmissionEventFactory())

    @factory.lazy_attribute
    def context(self):
        """Returns the context field"""
        return ContextFactory(path_tail="save_submission", **self.context_args)
