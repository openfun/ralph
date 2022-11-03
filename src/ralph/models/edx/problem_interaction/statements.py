"""Problem interaction events model definitions."""

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
    """Pydantic model for `edx.problem.hint.demandhint_displayed` statement.

    The server emits this statement when a user requests a hint for a problem.

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
    """Pydantic model for `edx.problem.hint.feedback_displayed` statement.

    The server emits this event when a user receives a hint after answering a problem.

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
    """Pydantic model for `problem_check` statement.

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
    """Pydantic model for `problem_check` statement.

    The server emits this event when a user checks a problem.

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
    """Pydantic model for `problem_check_fail` statement.

    The server emits this event when a user checks a problem and a failure prevents the
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
    """Pydantic model for `problem_graded` statement.

    The server emits this statement each time a user clicks <kbd>Check</kbd> for a
    problem and it is graded successfully.

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
    """Pydantic model for `problem_rescore` statement.

    The server emits this statement when a problem is successfully rescored.

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
    """Pydantic model for `problem_rescore_fail` statement.

    The server emits this statement when a problem cannot be successfully rescored.

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
    """Pydantic model for `problem_reset` statement.

    The browser emits problem_reset events when a user clicks <kbd>Reset</kbd> to reset
    the problem answer.

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
    """Pydantic model for `problem_save` statement.

    The browser emits this statement when a user saves a problem.

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
    """Pydantic model for `problem_show` statement.

    The browser emits this statement when the answer clicks <kbd>Show Answer</kbd> to
    show the problem answer.

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
    """Pydantic model for `reset_problem` statement.

    The server emits this statement when a problem has been reset successfully.

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
    """Pydantic model for `reset_problem_fail` statement.

    The server emits this statement when a problem cannot be reset successfully.

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
    """Pydantic model for `save_problem_fail` statement.

    The server emits this statement when a problem cannot be saved successfully.

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
    """Pydantic model for `save_problem_success` statement.

    The server emits this statement when a problem is saved successfully.

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
    """Pydantic model for `showanswer` statement.

    The server emits this statement when the answer to a problem is shown.

    Attributes:
        event (dict): See ShowAnswerEventField.
        event_type (str): Consists of the value `showanswer`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(event_source="server", event_type="showanswer")

    event: ShowAnswerEventField
    event_type: Literal["showanswer"]
    page: Literal["x_module"]
