"""Problem interaction events model event fields definitions."""

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import constr

from ...base import AbstractBaseEventField, BaseModelWithConfig


class QueueState(BaseModelWithConfig):
    """Represents the `queuestate` sub-field.

    Attributes:
        key (str): Consists of a secret string.
        time (str): Consists of a string dump of a DateTime object in the format
            '%Y%m%d%H%M%S'.
    """

    key: str
    time: datetime


class CorrectMap(BaseModelWithConfig):
    """Represents the `correct_map` sub-field.

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

    answervariable: Union[Literal[None], None, str]
    correctness: Union[Literal["correct"], Literal["incorrect"]]
    hint: Optional[str]
    hintmode: Optional[Union[Literal["on_request"], Literal["always"]]]
    msg: str
    npoints: Optional[int]
    queuestate: Optional[QueueState]


class State(BaseModelWithConfig):
    """Represents the `state` sub-field.

    Attributes:
        correct_map (dict): see CorrectMapSubFields.
        done (bool): `True` if the problem is answered, else `False`.
        input_state (dict): Consists of the state field given before answering.
        seed (int): Consists of the seed element for the current state.
        student_answers (dict): Consists of the answer(s) given by the user.
    """

    correct_map: dict[
        constr(regex=r"^[a-f0-9]{32}_[0-9]_[0-9]$"),  # noqa : F722
        CorrectMap,
    ]
    done: Optional[bool]
    input_state: dict
    seed: int
    student_answers: dict


class SubmissionAnswerField(BaseModelWithConfig):
    """Represents the information in a problem of `submission` field.

    Attributes:
        answer (str, list): Consists of the answer string or a list of the answer
            strings if multiple choices are allorwed.
        correct (bool): `True` if the `answer` value is correct, else `False`.
        input_type (str): Consists of the type of value that the student supplies for
            the `response_type`.
        question (str): Consists of the question text.
        response_type (str): Consists of the type of problem.
        variant (str): Consists of the unique ID of the variant that was presented to
            this user.
    """

    answer: Union[str, list[str]]
    correct: bool
    input_type: str
    question: str
    response_type: str
    variant: str


class EdxProblemHintDemandhintDisplayedEventField(AbstractBaseEventField):
    """Represents the `event` field of `EdxProblemHintDemandhintDisplayed` model.

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
    """Represents the `event` field of `EdxProblemHintFeedbackDisplayed` model.

    Attributes:
        choice_all (list): Lists all of the answer choices for problems with multiple
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

    choice_all: Optional[list[str]]
    correctness: bool
    hint_label: str
    hints: list[dict]
    module_id: str
    problem_part_id: str
    question_type: Union[
        Literal["stringresponse"],
        Literal["choiceresponse"],
        Literal["multiplechoiceresponse"],
        Literal["numericalresponse"],
        Literal["optionresponse"],
    ]
    student_answer: list[str]
    trigger_type: Union[Literal["single"], Literal["compound"]]


class ProblemCheckEventField(AbstractBaseEventField):
    """Represents the `event` field of `ProblemCheck` model.

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
        submission (dict): Consists of a dictionnary of data about the given answer.
        success (str): Consists of either the `correct` or `incorrect` value.
    """

    answers: dict[
        constr(regex=r"^[a-f0-9]{32}_[0-9]_[0-9]$"),  # noqa : F722
        Union[list[str], str],
    ]
    attempts: int
    correct_map: dict[
        constr(regex=r"^[a-f0-9]{32}_[0-9]_[0-9]$"),  # noqa : F722
        CorrectMap,
    ]
    grade: int
    max_grade: int
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )
    state: State
    submission: dict[
        constr(regex=r"^[a-f0-9]{32}_[0-9]_[0-9]$"),  # noqa : F722
        SubmissionAnswerField,
    ]
    success: Union[Literal["correct"], Literal["incorrect"]]


class ProblemCheckFailEventField(AbstractBaseEventField):
    """Represents the `event` field of `ProblemCheckFail` model.

    Attributes:
        answers (dict): Consists of a dictionary of problem ID and the internal answer
            identifier for each problem.
        failure (str): Consists either of the `closed` or `unreset` value.
        problem_id (str): Consists of the ID of the problem that was checked.
        state (dict): Consists of the current problem state.
    """

    answers: dict[
        constr(regex=r"^[a-f0-9]{32}_[0-9]_[0-9]$"),  # noqa : F722
        Union[list[str], str],
    ]
    failure: Union[Literal["closed"], Literal["unreset"]]
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )
    state: State


class ProblemRescoreEventField(AbstractBaseEventField):
    """Represents the `event` field of `ProblemRescore` model.

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
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )
    state: State
    success: Union[Literal["correct"], Literal["incorrect"]]


class ProblemRescoreFailEventField(AbstractBaseEventField):
    """Represents the `event` field of `ProblemRescoreFail` model.

    Attributes:
        failure (str): Consists either of the `closed` or `unreset` value.
        problem_id (str): Consists of the ID of the problem being checked.
        state (json): see StateField.
    """

    failure: Union[Literal["closed"], Literal["unreset"]]
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )
    state: State


class UIProblemResetEventField(AbstractBaseEventField):
    """Represents the `event` field of `ProblemReset` model.

    Attributes:
        answers (str, list): Consists of the answer string or a list of the answer
            strings if multiple choices are allowed.
    """

    answers: Union[str, list[str]]


class UIProblemShowEventField(AbstractBaseEventField):
    """Represents the `event` field of `ProblemShow` model.

    Attributes:
        problem (str): Consists of the optional name value that the course creators
            supply or the system-generated hash code for the problem being shown.
    """

    problem: str


class ResetProblemEventField(AbstractBaseEventField):
    """Represents the `event` field of `ResetProblem` model.

    Attributes:
        new_state (json): see StateField.
        old_state (json): see StateField.
        problem_id (str): Consists of the ID of the problem being reset.
    """

    new_state: State
    old_state: State
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )


class ResetProblemFailEventField(AbstractBaseEventField):
    """Represents the `event` field of `ResetProblemFail` model.

    Attributes:
        failure (str): Consists either of `closed` or `not_done` value.
        old_state (json): see StateField.
        problem_id (str): Consists of the ID of the problem being reset.
    """

    failure: Union[Literal["closed"], Literal["not_done"]]
    old_state: State
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )


class SaveProblemFailEventField(AbstractBaseEventField):
    """Represents the `event` field of `SaveProblemFail` model.

    Attributes:
        answers (dict): Consists of a dict of the answer string or a list or a dict of
            the answer strings if multiple choices are allowed.
        failure (str): Consists either of `closed` or `done` value.
        problem_id (str): Consists of the ID of the problem being saved.
        state (json): see StateField.
    """

    answers: dict[str, Union[int, str, list, dict]]
    failure: Union[Literal["closed"], Literal["done"]]
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )
    state: State


class SaveProblemSuccessEventField(AbstractBaseEventField):
    """Represents the `event` field of `SaveProblemSuccess` model.

    Attributes:
        answers (dict): Consists of a dict of the answer string or a list or a dict of
            the answer strings if multiple choices are allowed.
        problem_id (str): Consists of the ID of the problem being saved.
        state (json): see StateField.
    """

    answers: dict[str, Union[int, str, list, dict]]
    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )
    state: State


class ShowAnswerEventField(AbstractBaseEventField):
    """Represents the `event` field of `ShowAnswer` model.

    Attributes:
        problem_id (str): Consists of the ID of the problem being shown.
    """

    problem_id: constr(
        regex=r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"  # noqa : F722
        r"type@problem\+block@[a-f0-9]{32}$"  # noqa : F722
    )
