"""
problem_check triggered event fixture definition
"""

from faker import Faker

from .base import BaseEvent, EventFieldProperties, FreeEventField, TiedEventField
from .data import INPUT_TYPES, RESPONSE_TYPES
from .server import BaseTriggeredEvent

# Faker.seed(0)
FAKE = Faker()


class ProblemCheckEventField(BaseEvent):
    """Represents the Event Field of the problem_check event"""

    def __init__(self, *args, **kwargs):
        super(ProblemCheckEventField, self).__init__(*args, **kwargs)
        nb_of_questions = kwargs.get("set_nb_of_questions", FAKE.random_int(1, 10))
        if "correct_map" in self.kwargs:
            nb_of_questions = len(self.kwargs["correct_map"])
        nb_of_answers = kwargs.get(
            "set_nb_of_answers", FAKE.random_int(0, nb_of_questions)
        )
        self.correct_map = TiedEventField(
            self.get_correct_map,
            dependency=["context", "module", "usage_key"],
            nb_of_questions=nb_of_questions,
        )
        self.problem_id = TiedEventField(
            lambda x: x, dependency=["context", "module", "usage_key"]
        )
        self.max_grade = FAKE.random_int(1, 100)
        self.answers = TiedEventField(
            self.get_answers,
            dependency=["event", "correct_map"],
            nb_of_answers=nb_of_answers,
        )
        self.attempts = FAKE.random_int(1, 5)
        self.state = TiedEventField(
            self.get_state,
            dependency=[["context", "module", "usage_key"], ["event", "correct_map"]],
            nb_of_questions=nb_of_questions,
        )
        self.submission = TiedEventField(
            self.get_submission, dependency=[["event", "answers"], ["event", "state"]]
        )

    def get_submission(self, answers, state):
        """Returns the submission field which depends on the
        student answers and the current state
        """
        submission = {}
        for key in answers:
            input_type = FAKE.random_element(INPUT_TYPES)
            response_type = FAKE.random_element(RESPONSE_TYPES)
            if input_type == "formulaequationinput":
                response_type = FAKE.random_element(
                    ["numericalresponse", "formularesponse"]
                )
                answer = str(
                    FreeEventField(
                        FAKE.random_number,
                        properties=EventFieldProperties(emptiable_str=True),
                    ).get(*self.args)
                )
            if input_type == "optioninput":
                response_type = "optionresponse"
                answer = FreeEventField(
                    FAKE.word, properties=EventFieldProperties(emptiable_str=True)
                ).get(*self.args)
            if input_type == "checkboxgroup":
                response_type = "choiceresponse"
                answer = []
                for _ in range(FAKE.random_int(0, 10)):
                    answer.append(
                        FreeEventField(
                            FAKE.word,
                            properties=EventFieldProperties(emptiable_str=True),
                        ).get(*self.args)
                    )
            if input_type == "choicegroup":
                response_type = "multiplechoiceresponse"
                answer = FreeEventField(
                    FAKE.word, properties=EventFieldProperties(emptiable_str=True)
                ).get(*self.args)
            if input_type == "textline":
                response_type = "stringresponse"
                answer = FreeEventField(
                    FAKE.sentence, properties=EventFieldProperties(emptiable_str=True)
                ).get(*self.args)
            if input_type == "drag_and_drop_input":
                response_type = "customresponse"
                answer = "[" + FAKE.sentence() + "]"
            if input_type == "imageinput":
                response_type = "imageresponse"
                answer = "[" + FAKE.sentence() + "]"
            else:
                # I haven't tried other input/responses for now...
                answer = FreeEventField(
                    FAKE.sentence, properties=EventFieldProperties(emptiable_str=True)
                ).get(*self.args)

            submission[key] = {
                "question": FreeEventField(
                    FAKE.sentence, properties=EventFieldProperties(emptiable_str=True)
                ).get(*self.args),
                "answer": answer,
                "input_type": input_type,
                "response_type": response_type,
                "correct": FAKE.random_element(["", True, False]),
                "variant": "" if state["seed"] == 1 else state["seed"],
            }
        return submission

    def get_state(self, usage_key, correct_map, nb_of_questions):
        """Returns the state field which depends on the usage_key,
        the made correct_map and nb_of_questions option
        """
        input_state = {}
        for key in correct_map:
            input_state[key] = {}
        if self.attempts == 1:
            return {
                "student_answers": {},
                "seed": self.get_seed(),
                "done": None,
                "correct_map": {},
            }
        prev_correct_map = self.get_correct_map(usage_key, nb_of_questions)
        nb_of_prev_answers = FAKE.random_int(0, nb_of_questions)
        student_answers = self.get_answers(correct_map, nb_of_prev_answers)
        done = FAKE.random_element([None, True, False])
        return {
            "student_answers": student_answers,
            "seed": self.get_seed(),
            "done": done,
            "correct_map": prev_correct_map,
            "input_state": input_state,
        }

    def get_seed(self):
        """Returns the seed based on set_randomization_seed
        kwargs parameter
        """
        randomization = {
            "NEVER": 1,
            "PER_STUDENT": FAKE.random_int(0, 19),
            "OTHER": FAKE.random_int(0, 999),
        }
        return randomization.get(
            self.kwargs.get(
                "set_randomization_seed", FAKE.random_element(randomization.keys())
            ),
            FAKE.random_element(randomization.keys()),
        )

    def get_answers(self, correct_map, nb_of_answers):
        """Returns the answers event field dict"""
        answers_params = {
            "EMPTY": lambda: "",
            "MULTIPLE_CHOICE": self.get_multiple_choice_response,
            "NUMERICAL_INPUT": lambda: str(FAKE.random_number()),
            "DROP_DOWN": FAKE.sentence,
            "CHECKBOXES": self.get_checkboxes_response,
        }
        answers = {}
        keys = FAKE.random_elements(correct_map.keys(), nb_of_answers, unique=True)
        for key in keys:
            if "set_answer_types" in self.kwargs:
                if self.kwargs["set_answer_types"] in answers_params:
                    answers[key] = answers_params[self.kwargs["set_answer_types"]]()
                else:
                    answers[key] = self.kwargs["set_answer_types"]()
            else:
                answers[key] = FAKE.random_element(answers_params.values())()

        return answers

    def get_correct_map(self, usage_key, nb_of_questions):
        """Returns the correct_map event field dict"""
        correct_map = {}
        for i in range(0, nb_of_questions):
            key = "{}_{}_{}".format(usage_key[-32:], i + 1, 1)
            correct = FAKE.random_element(["correct", "incorrect", "partially-correct"])
            npoints = FreeEventField(
                lambda c=correct: FAKE.random_element([None, 0, 1])
                if c == "correct"
                else None,
                properties=EventFieldProperties(nullable=True),
            ).get(*self.args)
            msg = FreeEventField(
                FAKE.sentence, properties=EventFieldProperties(emptiable_str=True)
            ).get(*self.args)
            hint = FreeEventField(
                FAKE.sentence, properties=EventFieldProperties(emptiable_str=True)
            ).get(*self.args)
            hintmode = FAKE.random_element([None, "on_request", "always"])
            time = FAKE.date(pattern="%Y%m%d%H%M%S", end_datetime=None)
            secret = FAKE.md5(raw_output=False)
            queuestate = FreeEventField(
                lambda s=secret, t=time: {"key": s, "time": t},
                properties=EventFieldProperties(nullable=True),
            ).get(*self.args)
            correct_map[key] = {
                "correctness": correct,
                "npoints": npoints,
                "msg": msg,
                "hint": hint,
                "hintmode": hintmode,
                "queuestate": queuestate,
                "answervariable": None,
            }
        return correct_map

    @staticmethod
    def get_multiple_choice_response():
        """Returns a string representing a multiple choice response"""
        value = str(FAKE.random_int(0, 15)) if FAKE.boolean() else FAKE.word()
        return "choice_" + value

    @staticmethod
    def get_checkboxes_response():
        """Returns an array representing a checkbox response"""
        response = []
        for i in FAKE.random_elements(range(0, 15), unique=True):
            response.append("choice_" + str(i))
        return response


class ProblemCheckEvent(BaseTriggeredEvent):
    """Represents the problem_check triggered event
    This type of event is triggered when the user clicks on the
    sumbit button of a CAPA problem
    """

    def __init__(self, *args, **kwargs):
        super(ProblemCheckEvent, self).__init__(*args, **kwargs)
        self.context.path = self.context.path + "/problem_check"
        self.event = ProblemCheckEventField(*args, **kwargs.get("event", {}))
