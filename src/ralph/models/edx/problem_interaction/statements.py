"""Problem interaction events model definitions"""

from typing import Literal, Union

from pydantic import Json

from ralph.models.selector import selector

from ..browser import BaseBrowserModel
from ..server import BaseServerModel
from .fields.events import (
    EdxProblemHintDemandhintDisplayedEventField,
    EdxProblemHintFeedbackDisplayedEventField,
    ProblemCheckEventField,
    ProblemCheckFailEventField,
    ProblemRescoreEventField,
    ProblemRescoreFailEventField,
    ResetProblemEventField,
    ResetProblemFailEventField,
    SaveProblemFailEventField,
    SaveProblemSuccessEventField,
    ShowAnswerEventField,
    UIProblemResetEventField,
    UIProblemShowEventField,
)


class EdxProblemHintDemandhintDisplayed(BaseServerModel):
    """Represents the `edx.problem.hint.demandhint_displayed` server event.

    This event is triggered when a user requests a hint for a problem.

    Attributes:
        event (dict): See EdxProblemHintDemandhintDisplayedEventField.
        event_type (str): Consists of the value `edx.problem.hint.demandhint_displayed`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.problem.hint.demandhint_displayed"
    )

    event: EdxProblemHintDemandhintDisplayedEventField
    event_type: Literal["edx.problem.hint.demandhint_displayed"]
    page: Literal["x_module"]


class EdxProblemHintFeedbackDisplayed(BaseServerModel):
    """Represents the `edx.problem.hint.feedback_displayed` server event.

    This event is triggered when a user receives a hint after answering a problem.

    Attributes:
        event (dict): See EdxProblemHintFeedbackDisplayedEventField.
        event_type (str): Consists of the value `edx.problem.hint.feedback_displayed`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.problem.hint.feedback_displayed"
    )

    event: EdxProblemHintFeedbackDisplayedEventField
    event_type: Literal["edx.problem.hint.feedback_displayed"]
    page: Literal["x_module"]


class UIProblemCheck(BaseBrowserModel):
    """Represents the `problem_check` browser event.

    The browser emits this event when a user checks a problem.

    Attributes:
        event (str): Consists of values of problem being checked, styled as `GET`
            parameters.
        event_type (str): Consists of the value `problem_check`.
        name (str): Consists of the value `problem_check`.
    """

    __selector__ = selector(event_source="browser", event_type="problem_check")

    event: str
    event_type: Literal["problem_check"]
    name: Literal["problem_check"]


class ProblemCheck(BaseServerModel):
    """Represents the `problem_check` server event.

    This event is triggered when a user checks a problem.

    Attributes:
        event (dict): See ProblemCheckEventField.
        event_type (str): Consists of the value `problem_check`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="problem_check")

    event: ProblemCheckEventField
    event_type: Literal["problem_check"]
    page: Literal["x_module"]


class ProblemCheckFail(BaseServerModel):
    """Represents the `problem_check_fail` server event.

    This event is triggered when a user checks a problem and a failure prevents the
    problem from being checked successfully.

    Attributes:
        event (dict): See ProblemCheckFailEventField.
        event_type (str): Consists of the value `problem_check_fail`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="problem_check_fail")

    event: ProblemCheckFailEventField
    event_type: Literal["problem_check_fail"]
    page: Literal["x_module"]


class UIProblemGraded(BaseBrowserModel):
    """Represents the `problem_graded` browser event.

    Attributes:
        event (list): See ProblemGradedEventField.
        event_type (str): Consists of the value `problem_graded`.
        name (str): Consists of the value `problem_graded`.
    """

    __selector__ = selector(event_source="browser", event_type="problem_graded")

    event: list[Union[str, Literal[None], None]]
    event_type: Literal["problem_graded"]
    name: Literal["problem_graded"]


class ProblemRescore(BaseServerModel):
    """Represents the `problem_rescore` server event.

    Attributes:
        event (dict): See ProblemRescoreEventField.
        event_type (str): Consists of the value `problem_rescore`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="problem_rescore")

    event: ProblemRescoreEventField
    event_type: Literal["problem_rescore"]
    page: Literal["x_module"]


class ProblemRescoreFail(BaseServerModel):
    """Represents the `problem_rescore_fail` server event.

    Attributes:
        event (dict): See ProblemRescoreFailEventField.
        event_type (str): Consists of the value `problem_rescore_fail`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="problem_rescore_fail")

    event: ProblemRescoreFailEventField
    event_type: Literal["problem_rescore_fail"]
    page: Literal["x_module"]


class UIProblemReset(BaseBrowserModel):
    """Represents the `problem_reset` browser event.

    Attributes:
        event (json): See ProblemResetEventField.
        event_type (str): Consists of the value `problem_reset`.
        name (str): Consists of the value `problem_reset`.
    """

    __selector__ = selector(event_source="browser", event_type="problem_reset")

    event: Union[
        str,
        Json[UIProblemResetEventField],  # pylint: disable=unsubscriptable-object
        UIProblemResetEventField,
    ]
    event_type: Literal["problem_reset"]
    name: Literal["problem_reset"]


class UIProblemSave(BaseBrowserModel):
    """Represents the `problem_save` browser event.

    Attributes:
        event (str): Consists of all the answers saved for the problem.
        event_type (str): Consists of the value `problem_save`.
        name (str): Consists of the value `problem_save`.
    """

    __selector__ = selector(event_source="browser", event_type="problem_save")

    event: str
    event_type: Literal["problem_save"]
    name: Literal["problem_save"]


class UIProblemShow(BaseBrowserModel):
    """Represents the `problem_show` browser event.

    Attributes:
        event (json): See ProblemShowEventField.
        event_type (str): Consists of the value `problem_save`.
        name (str): Consists of the value `problem_save`.
    """

    __selector__ = selector(event_source="browser", event_type="problem_show")

    event: Union[
        Json[UIProblemShowEventField],  # pylint: disable=unsubscriptable-object
        UIProblemShowEventField,
    ]
    event_type: Literal["problem_show"]
    name: Literal["problem_show"]


class ResetProblem(BaseServerModel):
    """Represents the `reset_problem` server event.

    Attributes:
        event (dict): See ResetProblemEventField.
        event_type (str): Consists of the value `reset_problem`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="reset_problem")

    event: ResetProblemEventField
    event_type: Literal["reset_problem"]
    page: Literal["x_module"]


class ResetProblemFail(BaseServerModel):
    """Represents the `reset_problem_fail` server event.

    Attributes:
        event (dict): See ResetProblemFailEventField.
        event_type (str): Consists of the value `reset_problem_fail`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="reset_problem_fail")

    event: ResetProblemFailEventField
    event_type: Literal["reset_problem_fail"]
    page: Literal["x_module"]


class SaveProblemFail(BaseServerModel):
    """Represents the `save_problem_fail` server event.

    Attributes:
        event (dict): See SaveProblemFailEventField.
        event_type (str): Consists of the value `save_problem_fail`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="save_problem_fail")

    event: SaveProblemFailEventField
    event_type: Literal["save_problem_fail"]
    page: Literal["x_module"]


class SaveProblemSuccess(BaseServerModel):
    """Represents the `save_problem_success` server event.

    Attributes:
        event (dict): See SaveProblemSuccessEventField.
        event_type (str): Consists of the value `save_problem_success`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="save_problem_success")

    event: SaveProblemSuccessEventField
    event_type: Literal["save_problem_success"]
    page: Literal["x_module"]


class ShowAnswer(BaseServerModel):
    """Represents the `showanswer` server event.

    Attributes:
        event (dict): See ShowAnswerEventField.
        event_type (str): Consists of the value `showanswer`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="showanswer")

    event: ShowAnswerEventField
    event_type: Literal["showanswer"]
    page: Literal["x_module"]
