"""
edx.problem.hint.feedback_displayed event factory definition
"""
import factory
from faker import Faker

from ralph.schemas.edx.feedback_displayed import (
    FeedbackDisplayedEventSchema,
    FeedbackDisplayedSchema,
)

from .base import BaseEventFactory, BaseFactory, ContextFactory

# pylint: disable=no-member, comparison-with-callable

FAKE = Faker()


class FeedbackDisplayedEventFactory(BaseFactory):
    """Represents the Event Field factory of an
    edx.problem.hint.feedback_displayed event
    """

    class Meta:  # pylint: disable=missing-class-docstring
        model = FeedbackDisplayedEventSchema

    class Params:  # pylint: disable=missing-class-docstring
        context = {}
        is_choiceresponse = False

    correctness = factory.Sequence(lambda n: FAKE.boolean())

    @factory.lazy_attribute
    def hint_label(self):
        """Returns the hint_label field which depends on the correctness"""
        if self.correctness:
            return "Correct"
        return FAKE.random_element(["Incorrect", FAKE.sentence()])

    @factory.lazy_attribute
    def module_id(self):
        """Returns the module_id filed which is equal to the
        context.module.usage_key
        """
        return self.context["module"]["usage_key"]

    @factory.lazy_attribute
    def problem_part_id(self):
        """Returns the problem_part_id field which depends on the
        event module_id
        """
        return f"{self.module_id[-32:]}_{str(FAKE.random_int(max=10))}"

    @factory.lazy_attribute
    def question_type(self):
        """Returns the question_type field"""
        if self.is_choiceresponse:
            return "choiceresponse"
        return FAKE.random_element(
            [
                "optionresponse",
                "multiplechoiceresponse",
                "numericalresponse",
                "stringresponse",
            ]
        )

    @factory.lazy_attribute
    def trigger_type(self):
        """Returns the trigger_type field value.
        For all questions except the choiceresponse it's value is single
        For choiceresponse questions it might be "compound" if the
        the teacher put in place a compound feedback
        """
        if self.question_type != "choiceresponse":
            return "single"
        return "compound" if FAKE.boolean() else "single"

    @factory.lazy_attribute
    def student_answer(self):
        """Returns an array representing the student_answer field
        depends on trigger_type and question_type
        """
        is_compound = self.trigger_type == "compound"
        if FAKE.boolean() and not is_compound:
            return []
        if self.question_type == "multiplechoiceresponse":
            return ["choice_{}".format(FAKE.random_int(0, 15))]
        if self.question_type == "numericalresponse":
            return ["{}".format(FAKE.random_number())]
        if self.question_type in ["stringresponse", "optionresponse"]:
            return [FAKE.random_element([FAKE.word(), FAKE.sentence()])]
        # choiceresponse
        student_answer = []
        for i in sorted(FAKE.random_elements(elements=list(range(15)), unique=True)):
            student_answer.append("choice_{}".format(i))
        return student_answer

    @factory.lazy_attribute
    def hints(self):
        """Returns the hints array which depends on
        question_type, trigger_type, student_answer
        """
        hints = []
        is_single_hint = self.question_type in [
            "optionresponse",
            "stringresponse",
            "numericalresponse",
            "multiplechoiceresponse",
        ]
        if is_single_hint:
            hints.append({"text": FAKE.sentence()})
            return hints
        is_compound = self.trigger_type == "compound"
        for i in sorted(FAKE.random_elements(elements=list(range(15)), unique=True)):
            choice = "choice_{}".format(i)
            hint = {
                "text": FAKE.sentence(),
                "trigger": [
                    {"selected": choice in self.student_answer, "choice": choice}
                ],
            }
            if is_compound:
                new_trigger = []
                for answer in self.student_answer:
                    new_trigger.append({"selected": True, "choice": answer})
                hint["trigger"] = new_trigger
                hints.append(hint)
                break
            hints.append(hint)

        return hints

    @factory.lazy_attribute
    def choice_all(self):
        """Returns an array representing the choice_all field"""
        if self.question_type != "choiceresponse":
            # this event field will not be present
            FeedbackDisplayedEventFactory._meta.exclude = "choice_all"
            return []
        # hints = [{
        #   "trigger": [
        #       {"selected": bool, "choice": "choice_{int_first}"},
        #       ...
        #       {"selected": bool, "choice": "choice_{int_last}"}
        #   ]
        # }]
        # pylint: disable=unsubscriptable-object
        last_choice = int(self.hints[-1]["trigger"][-1]["choice"][7:])
        size = FAKE.random_int(min=last_choice, max=15)
        choice_all = []
        for i in range(size):
            choice_all.append("choice_{}".format(i))
        return choice_all


class FeedbackDisplayedFactory(BaseEventFactory):
    """Represents the edx.problem.hint.feedback_displayed event factory"""

    class Meta:  # pylint: disable=missing-class-docstring
        model = FeedbackDisplayedSchema

    class Params:  # pylint: disable=missing-class-docstring
        context_args = {}
        event_args = {}

    username = factory.Sequence(lambda n: FAKE.profile().get("username"))
    event_type = "edx.problem.hint.feedback_displayed"
    page = "x_module"

    @factory.lazy_attribute
    def context(self):
        """Returns the context field"""
        return ContextFactory(
            path_tail="xmodule_handler/problem_check", **self.context_args
        )

    @factory.lazy_attribute
    def event(self):
        """Returns the event field"""
        is_choiceresponse = FAKE.boolean(chance_of_getting_true=20)
        if "question_type" in self.event_args:
            is_choiceresponse = self.event_args["question_type"] == "choiceresponse"
        # pylint: disable=protected-access
        FeedbackDisplayedEventFactory._meta.exclude = ()
        if not is_choiceresponse:
            # pylint: disable=protected-access
            FeedbackDisplayedEventFactory._meta.exclude = "choice_all"
        return FeedbackDisplayedEventFactory(
            context=self.context, is_choiceresponse=is_choiceresponse, **self.event_args
        )
