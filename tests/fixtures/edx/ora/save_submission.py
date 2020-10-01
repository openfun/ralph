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

from ..base import _ContextFactory
from ..mixins import JSONFactoryMixin, ObjFactoryMixin
from .base_ora_event import _BaseOraEventFactory

FAKE = Faker()


class _SaveSubmissionEventFactory(ObjFactoryMixin, factory.Factory):
    """Represents the Event Field factory of an
    openassessmentblock.save_submission
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = SaveSubmissionEventSchema

    @factory.sequence
    def saved_response(number):  # pylint: disable=no-self-argument, no-self-use
        """ returns the saved_response field"""
        parts_value = []
        for _ in range(FAKE.random_digit_not_null()):
            parts_value.append({"text": FAKE.sentence()})
        saved_response = {"parts": parts_value}
        return json.dumps(saved_response)


class _SaveSubmissionFactory(_BaseOraEventFactory):
    """Represents the openassessmentblock.save_submission event factory"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = SaveSubmissionSchema

    event_type = "openassessmentblock.save_submission"
    event = factory.Sequence(lambda n: _SaveSubmissionEventFactory())

    @factory.lazy_attribute
    # pylint: disable=no-member
    def context(self):
        """Returns the context field"""
        return _ContextFactory(path_tail="save_submission", **self.context_args)


class SaveSubmissionStrFactory(JSONFactoryMixin, _SaveSubmissionFactory):
    """ Creates JSON Serialized model of the factory data """


class SaveSubmissionObjFactory(ObjFactoryMixin, _SaveSubmissionFactory):
    """ Creates Deserialized model of the factory data """
