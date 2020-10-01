"""
openassessmentblock.create_submission event factory definition
"""
from enum import Enum, auto

import factory
from faker import Faker

from ralph.schemas.edx.ora.create_submission import (
    CreateSubmissionEventAnswerSchema,
    CreateSubmissionEventSchema,
    CreateSubmissionSchema,
)

from ..base import _ContextFactory
from ..mixins import JSONFactoryMixin, ObjFactoryMixin
from .base_ora_event import _BaseOraEventFactory

FAKE = Faker()


class CreateSubmissionType(Enum):
    """Represents a list of defined Event Types"""

    TEXT = auto()
    FILE = auto()
    TEXT_AND_FILE = auto()


class _CreateSubmissionEventAnswerFactory(ObjFactoryMixin, factory.Factory):
    """Represents the answer field of the event field
    of an openassessementblock.create_submission event
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = CreateSubmissionEventAnswerSchema

    class Params:  # pylint: disable=missing-class-docstring
        submission_type = CreateSubmissionType.TEXT_AND_FILE.value

    # pylint: disable=no-self-argument, no-self-use, no-member

    @factory.sequence
    def files_descriptions(number):
        """Represents the file_descriptions field.
        - It's abcent if the exercice don't permit file submissions
        - It's an empty array if no files were submitted
        - Else it's an array of strings representing the description
        for each submitted file
        """
        descriptions = []
        for _ in range(FAKE.random_int(max=20)):
            descriptions.append(FAKE.sentence())
        return descriptions

    @factory.lazy_attribute
    def file_keys(self):
        """Represents the file_keys field.
        - It's abcent if the exercice don't permit file submissions
        - It's an empty array if no files were submitted
        - Else it's an array of strings representing a URL for each submitted file
        """
        keys = []
        # pylint: disable=not-an-iterable
        for _ in self.files_descriptions:
            keys.append(FAKE.sentence())
        return keys

    @factory.lazy_attribute
    def parts(self):
        """Represents the parts field. It's always present and contains the
        text of the answer to the openassessment exercice.
        - It's an empty array if the exercice don't include text submission
        - Else it contains objects with key "text" and the text submission as their value
        """
        if self.submission_type == CreateSubmissionType.FILE.value:
            return []
        parts_array = []
        for text in FAKE.texts(nb_texts=FAKE.random_digit(), max_nb_chars=200):
            parts_array.append({"text": text})
        return parts_array


class _CreateSubmissionEventFactory(ObjFactoryMixin, factory.Factory):
    """Represents the Event Field factory of an
    openassessmentblock.create_submission
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = CreateSubmissionEventSchema

    class Params:  # pylint: disable=missing-class-docstring
        submission_type = CreateSubmissionType.TEXT_AND_FILE.value

    attempt_number = factory.Sequence(lambda n: FAKE.random_int())
    submitted_at = factory.Sequence(lambda n: FAKE.iso8601())
    submission_uuid = factory.Sequence(lambda n: FAKE.uuid4())
    created_at = factory.Sequence(lambda n: FAKE.iso8601())

    # pylint: disable=no-member

    @factory.lazy_attribute
    def answer(self):
        """Returns the answer field"""
        # pylint: disable=protected-access
        _CreateSubmissionEventAnswerFactory._meta.exclude = ()
        if self.submission_type == CreateSubmissionType.TEXT.value:
            _CreateSubmissionEventAnswerFactory._meta.exclude = (
                "file_keys",
                "files_descriptions",
            )
        return _CreateSubmissionEventAnswerFactory(submission_type=self.submission_type)


class _CreateSubmissionFactory(_BaseOraEventFactory):
    """Represents the openassessmentblock.create_submission event factory"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = CreateSubmissionSchema

    class Params:  # pylint: disable=missing-class-docstring
        submission_type = CreateSubmissionType.TEXT_AND_FILE.value

    event_type = "openassessmentblock.create_submission"
    event = factory.LazyAttribute(
        lambda o: _CreateSubmissionEventFactory(submission_type=o.submission_type)
    )

    # pylint: disable=no-member

    @factory.lazy_attribute
    def context(self):
        """Returns the context field"""
        return _ContextFactory(path_tail="submit", **self.context_args)


class CreateSubmissionStrFactory(JSONFactoryMixin, _CreateSubmissionFactory):
    """ Creates JSON Serialized model of the factory data """


class CreateSubmissionObjFactory(ObjFactoryMixin, _CreateSubmissionFactory):
    """ Creates Deserialized model of the factory data """
