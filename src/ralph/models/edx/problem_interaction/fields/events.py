"""Problem interaction events model event fields definitions."""

import sys
from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import Field
from typing_extensions import Annotated

from ...base import AbstractBaseEventField, BaseModelWithConfig

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class QueueState(BaseModelWithConfig):
    """Pydantic model for problem interaction `event`.`correct_map`.`queuestate` field.

    Attributes:
        key (str): Consists of a secret string.
        time (str): Consists of a string dump of a DateTime object in the format
            '%Y%m%d%H%M%S'.
    """

    key: str
    time: datetime


class CorrectMap(BaseModelWithConfig):
    """Pydantic model for problem interaction `event`.`correct_map` field.

    Attributes:
        answervariable (str): Consists of the variable chosen in answer in the case of
            optionresponse provided with variables.
        correctness (str): Consists either of the `correct` or `incorrect` value.
        hint (str): Consists of optional hint.
        hint_mode (str): Consists either of the value `on_request` or `always` value.
        msg (str): Consists of extra message response.
        npoints (int): Consists of awarded points.
        queuestate (json): see QueueStateField.
    """

    answervariable: Optional[str] = None
    correctness: Literal["correct", "incorrect"]
    hint: Optional[str] = None
    hintmode: Optional[Literal["on_request", "always"]] = None
    msg: str
    npoints: Optional[int] = None
    queuestate: Optional[QueueState] = None


class State(BaseModelWithConfig):
    """Pydantic model for problem interaction `event`.`state` field.

    Attributes:
        correct_map (dict): see CorrectMapSubFields.
        done (bool): `True` if the problem is answered, else `False`.
        input_state (dict): Consists of the state field given before answering.
        seed (int): Consists of the seed element for the current state.
        student_answers (dict): Consists of the answer(s) given by the user.
    """

    correct_map: Dict[
        Annotated[str, Field(pattern=r"^[a-f0-9]{32}_[0-9]_[0-9]$")],
        CorrectMap,
    ]
    done: Optional[bool] = None
    input_state: dict
    seed: int
    student_answers: dict


class SubmissionAnswerField(BaseModelWithConfig):
    """Pydantic model for `problem_check`.`event`.`submission` field.

    Attributes:
        answer (str, list): Consists of the answer string or a list of the answer
            strings if multiple choices are allowed.
        correct (bool): `True` if the `answer` value is correct, else `False`.
        input_type (str): Consists of the type of value that the student supplies for
            the `response_type`.
        question (str): Consists of the question text.
        response_type (str): Consists of the type of problem.
        variant (str): Consists of the unique ID of the variant that was presented to
            this user.
    """

    answer: Union[str, List[str]]
    correct: bool
    input_type: str
    question: str
    response_type: str
    variant: str


class EdxProblemHintDemandhintDisplayedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.problem.hint.demandhint_displayed`.`event` field.

    Attributes:
        hint_index (int): Consists of the identifier for the hint that was displayed to
            the user.
        hint_len (int): Consists of the total number of hints defined for this problem.
        hint_text (str): Consists of the text of the hint that was displayed to the
            user.
        module_id (str): Consists of the identifier for the problem component for which
            the user requested the hint.
    """

    hint_index: int
    hint_len: int
    hint_text: str
    module_id: str


class EdxProblemHintFeedbackDisplayedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.problem.hint.feedback_displayed`.`event` field.

    Attributes:
        choice_all (list): Lists all the answer choices for problems with multiple
            possible answers defined.
        correctness (bool): `True` if the `student_answer` value is correct, else
            `False`.
        hint_label (str): Consists of the feedback message given for the answer
            correctness.
        hints (list): Consists of a text member field with the given feedback string.
        module_id (str): Consists of the identifier for the problem component for which
            the user received the feedback.
        problem_part_id (str): Consists of the specific problem for which the user
            received feedback.
        question_type (str): Consists of the XML tag that identifies the problem type.
        student_answer (list): Consists of the answer value(s) selected or supplied by
            the user.
        trigger_type (str): Identifies the type of feedback obtained by the
            `student_answer` response. Consists either of `single` or `compound` value.
    """

    choice_all: Optional[List[str]] = None
    correctness: bool
    hint_label: str
    hints: List[dict]
    module_id: str
    problem_part_id: str
    question_type: Literal[
        "stringresponse",
        "choiceresponse",
        "multiplechoiceresponse",
        "numericalresponse",
        "optionresponse",
    ]
    student_answer: List[str]
    trigger_type: Literal["single", "compound"]


class ProblemCheckEventField(AbstractBaseEventField):
    """Pydantic model for `problem_check`.`event` field.

    Attributes:
        answers (dict): Consists of a dictionary of problem ID and the corresponding
            internal answer identifier for each problem.
        attempts (int): Consists of the number of times the user attempted to answer
            the problem.
        correct_map (dict): Consists of the evaluation data for each answer.
        grade (int): Consists of the current grade value.
        max_grade (int): Consists of the maximum possible grade value.
        problem_id (str): Consists of the ID of the problem that was checked.
        state (json): Consists of the current problem state.
        submission (dict): Consists of a dictionary of data about the given answer.
        success (str): Consists of either the `correct` or `incorrect` value.
    """

    answers: Dict[
        Annotated[str, Field(pattern=r"^[a-f0-9]{32}_[0-9]_[0-9]$")],
        Union[str, List[str]],
    ]
    attempts: int
    correct_map: Dict[
        Annotated[str, Field(pattern=r"^[a-f0-9]{32}_[0-9]_[0-9]$")],
        CorrectMap,
    ]
    grade: int
    max_grade: int
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]
    state: State
    submission: Dict[
        Annotated[str, Field(pattern=r"^[a-f0-9]{32}_[0-9]_[0-9]$")],
        SubmissionAnswerField,
    ]
    success: Literal["correct", "incorrect"]


class ProblemCheckFailEventField(AbstractBaseEventField):
    """Pydantic model for `problem_check_fail`.`event` field.

    Attributes:
        answers (dict): Consists of a dictionary of problem ID and the internal answer
            identifier for each problem.
        failure (str): Consists either of the `closed` or `unreset` value.
        problem_id (str): Consists of the ID of the problem that was checked.
        state (dict): Consists of the current problem state.
    """

    answers: Dict[
        Annotated[str, Field(pattern=r"^[a-f0-9]{32}_[0-9]_[0-9]$")],
        Union[str, List[str]],
    ]
    failure: Literal["closed", "unreset"]
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]
    state: State


class ProblemRescoreEventField(AbstractBaseEventField):
    """Pydantic model for `problem_rescore`.`event` field.

    Attributes:
        attempts (int): Consists of the number of attempts of rescoring.
        correct_map (json): see CorrectMapSubFields.
        new_score (int): Consists of the new score obtained after rescoring.
        new_total (int): Consists of the new total summed after rescoring.
        orig_score (int): Consists of the original scored before rescoring.
        problem_id (str): Consists of the ID of the problem being rescored.
        state (json): see StateField.
        success (str): Consists either of the `correct` or `incorrect` value.
    """

    attempts: int
    correct_map: CorrectMap
    new_score: int
    new_total: int
    orig_score: int
    orig_total: int
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]
    state: State
    success: Literal["correct", "incorrect"]


class ProblemRescoreFailEventField(AbstractBaseEventField):
    """Pydantic model for `problem_rescore_fail`.`event` field.

    Attributes:
        failure (str): Consists either of the `closed` or `unreset` value.
        problem_id (str): Consists of the ID of the problem being checked.
        state (json): see StateField.
    """

    failure: Literal["closed", "unreset"]
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]
    state: State


class UIProblemResetEventField(AbstractBaseEventField):
    """Pydantic model for `problem_reset`.`event` field.

    Attributes:
        answers (str, list): Consists of the answer string or a list of the answer
            strings if multiple choices are allowed.
    """

    answers: Union[str, List[str]]


class UIProblemShowEventField(AbstractBaseEventField):
    """Pydantic model for `problem_show`.`event` field.

    Attributes:
        problem (str): Consists of the optional name value that the course creators
            supply or the system-generated hash code for the problem being shown.
    """

    problem: str


class ResetProblemEventField(AbstractBaseEventField):
    """Pydantic model for `reset_problem`.`event` field.

    Attributes:
        new_state (json): see StateField.
        old_state (json): see StateField.
        problem_id (str): Consists of the ID of the problem being reset.
    """

    new_state: State
    old_state: State
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]


class ResetProblemFailEventField(AbstractBaseEventField):
    """Pydantic model for `reset_problem_fail`.`event` field.

    Attributes:
        failure (str): Consists either of `closed` or `not_done` value.
        old_state (json): see StateField.
        problem_id (str): Consists of the ID of the problem being reset.
    """

    failure: Literal["closed", "not_done"]
    old_state: State
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]


class SaveProblemFailEventField(AbstractBaseEventField):
    """Pydantic model for `save_problem_fail`.`event` field.

    Attributes:
        answers (dict): Consists of a dict of the answer string or a list or a dict of
            the answer strings if multiple choices are allowed.
        failure (str): Consists either of `closed` or `done` value.
        problem_id (str): Consists of the ID of the problem being saved.
        state (json): see StateField.
    """

    answers: Dict[str, Union[int, str, list, dict]]
    failure: Literal["closed", "done"]
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]
    state: State


class SaveProblemSuccessEventField(AbstractBaseEventField):
    """Pydantic model for `save_problem_success`.`event` field.

    Attributes:
        answers (dict): Consists of a dict of the answer string or a list or a dict of
            the answer strings if multiple choices are allowed.
        problem_id (str): Consists of the ID of the problem being saved.
        state (json): see StateField.
    """

    answers: Dict[str, Union[int, str, list, dict]]
    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]
    state: State


class ShowAnswerEventField(AbstractBaseEventField):
    """Pydantic model for `show_answer`.`event` field.

    Attributes:
        problem_id (str): Consists of the ID of the problem being shown.
    """

    problem_id: Annotated[
        str,
        Field(
            pattern=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
            r"type@problem\+block@[a-f0-9]{32}$"
        ),
    ]
