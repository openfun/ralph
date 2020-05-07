"""
edx.problem.hint.feedback_displayed event fixture definition
"""

from faker import Faker

from .base import BaseEvent, FreeEventField, TiedEventField
from .server import BaseServerEvent, BaseTriggeredEvent

# Faker.seed(0)
FAKE = Faker()


class FeedbackDisplayedEventField(BaseEvent):
    """Represents the event field of an
    edx.problem.hint.feedback_displayed
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kwargs):
        super(FeedbackDisplayedEventField, self).__init__(*args, **kwargs)
        self.correctness = FAKE.boolean()
        self.hint_label = TiedEventField(
            self.get_hint_label, dependency=["event", "correctness"]
        )
        self.module_id = TiedEventField(
            BaseServerEvent.get_module_id, dependency="context"
        )
        self.problem_part_id = self.module_id[-32:] + "_" + str(FAKE.random_int(max=10))
        self.question_type = FAKE.random_element(
            [
                "choiceresponse",
                "optionresponse",
                "multiplechoiceresponse",
                "numericalresponse",
                "stringresponse",
            ]
        )
        self.student_answer = TiedEventField(
            self.get_student_answer, dependency=["event", "question_type"]
        )
        self.hints = TiedEventField(
            self.get_hints,
            dependency=[
                ["event", "question_type"],
                ["event", "trigger_type"],
                ["event", "student_answer"],
            ],
        )
        self.trigger_type = TiedEventField(
            self.get_trigger_type,
            dependency=[["event", "question_type"], ["event", "student_answer"]],
        )
        # This EventField might be "removed"
        self.choice_all = TiedEventField(
            self.get_choice_all,
            dependency=[["event", "question_type"], ["event", "student_answer"]],
        )

    @staticmethod
    def get_trigger_type(question_type, student_answer):
        """Returns the trigger_type field value.
        For all questions except the choiceresponse it's value is single
        For choiceresponse questions it might be "compound" if the
        the teacher put in place a compound feedback
        """
        if question_type != "choiceresponse" or len(student_answer) == 0:
            return "single"
        return "compound" if FAKE.boolean() else "single"

    @staticmethod
    def get_hint_label(correctness):
        """Returns the hint_label field which depends on the correctness"""
        if correctness:
            return "Correct"
        return FAKE.random_element(["Incorrect", FAKE.sentence()])

    @staticmethod
    def get_hints(question_type, trigger_type, student_answer):
        """Returns the hints array"""
        hints = []
        is_single_hint = question_type in [
            "optionresponse",
            "stringresponse",
            "numericalresponse",
            "multiplechoiceresponse",
        ]
        if is_single_hint:
            hints.append({"text": FAKE.sentence()})
            return hints
        is_compound = trigger_type == "compound"
        max_nb_of_hints = FAKE.random_int(1, 15)
        not_skipped_hint = FAKE.random_int(1, max_nb_of_hints)
        for i in range(max_nb_of_hints):
            if FAKE.boolean() or is_compound or i == not_skipped_hint:
                hint = {
                    "text": FAKE.sentence(),
                    "trigger": [
                        {"selected": FAKE.boolean(), "choice": "choice_{}".format(i)}
                    ],
                }
                if is_compound:
                    new_trigger = []
                    for answer in student_answer:
                        new_trigger.append({"selected": True, "choice": answer})
                    hint["trigger"] = new_trigger
                    hints.append(hint)
                    break
                hints.append(hint)

        return hints

    @staticmethod
    def get_student_answer(question_type):
        """Returns an array representing the student_answer field"""
        student_answer = []
        if FAKE.boolean():
            return student_answer
        for i in range(FAKE.random_int(0, 5)):
            if question_type in ["choiceresponse", "multiplechoiceresponse"]:
                student_answer.append("choice_{}".format(i))
            elif question_type == "numericalresponse":
                student_answer.append("{}".format(FAKE.random_number()))
                break
            else:
                student_answer.append(
                    FAKE.random_element([FAKE.word(), FAKE.sentence()])
                )
                break
        return student_answer

    @staticmethod
    def get_choice_all(question_type, student_answer):
        """Returns an array representing the choice_all field"""
        if question_type != "choiceresponse":
            # this event field will not be present
            return FreeEventField(lambda: None)
        size = FAKE.random_int(min=len(student_answer), max=10)
        choice_all = []
        for i in range(size):
            choice_all.append("choice_{}".format(i))
        return choice_all


class FeedbackDisplayedEvent(BaseTriggeredEvent):
    """Represents the edx.problem.hint.feedback_displayed event
    This type of event is triggered after the user submits an answer
    for a problem that include feedback messages
    """

    def __init__(self, *args, **kwargs):
        super(FeedbackDisplayedEvent, self).__init__(*args, **kwargs)
        self.context.path = self.context.path + "/problem_check"
        self.event = FeedbackDisplayedEventField(*args, **kwargs.get("event", {}))
