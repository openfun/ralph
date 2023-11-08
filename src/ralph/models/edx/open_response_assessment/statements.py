"""Open Response Assessment events model definitions."""

import sys
from typing import Union

from pydantic import Json

from ralph.models.edx.browser import BaseBrowserModel
from ralph.models.edx.server import BaseServerModel
from ralph.models.selector import selector

from .fields.events import (
    ORAAssessEventField,
    ORACreateSubmissionEventField,
    ORAGetPeerSubmissionEventField,
    ORAGetSubmissionForStaffGradingEventField,
    ORASaveSubmissionEventField,
    ORAStaffAssessEventField,
    ORAStudentTrainingAssessExampleEventField,
    ORASubmitFeedbackOnAssessmentsEventField,
    ORAUploadFileEventField,
)

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class ORAGetPeerSubmission(BaseServerModel):
    """Pydantic model for `openassessmentblock.get_peer_submission` statement.

    The server emits this statement when a response is delivered to a learner for
    evaluation.

    Attributes:
        event (dict): See ORAGetPeerSubmissionEventField.
        event_type (str): Consists of the value
            `openassessmentblock.get_peer_submission`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.get_peer_submission"
    )

    event: ORAGetPeerSubmissionEventField
    event_type: Literal["openassessmentblock.get_peer_submission"]
    page: Literal["x_module"]


class ORAGetSubmissionForStaffGrading(BaseServerModel):
    """Pydantic model for `openassessmentblock.get_submission_for_staff_grading`
    statement.

    The server emits this statement when a course team member retrieves a learner's
    response for grading.

    Attributes:
        event (dict): See ORAGetSubmissionForStaffGradingEventField.
        event_type (str): Consists of the value
            `openassessmentblock.get_submission_for_staff_grading`.
        page (str): Consists of the value `x_module`.
    """  # noqa: D205

    __selector__ = selector(
        event_source="server",
        event_type="openassessmentblock.get_submission_for_staff_grading",
    )

    event: ORAGetSubmissionForStaffGradingEventField
    event_type: Literal["openassessmentblock.get_submission_for_staff_grading"]
    page: Literal["x_module"]


class ORAPeerAssess(BaseServerModel):
    """Pydantic model for `openassessmentblock.peer_assess` statement.

    The server emits this statement when a learner submits an assessment of a
    peer's response.

    Attributes:
        event (dict): See ORAAssessEventField.
        event_type (str): Consists of the value `openassessmentblock.peer_assess`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.peer_assess"
    )

    event: ORAAssessEventField
    event_type: Literal["openassessmentblock.peer_assess"]
    page: Literal["x_module"]


class ORASelfAssess(BaseServerModel):
    """Pydantic model for `openassessmentblock.self_assess` statement.

    The server emits this statement when a learner submits a self-assessment.

    Attributes:
        event (dict): See ORAAssessEventField.
        event_type (str): Consists of the value `openassessmentblock.self_assess`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.self_assess"
    )

    event: ORAAssessEventField
    event_type: Literal["openassessmentblock.self_assess"]
    page: Literal["x_module"]


class ORAStaffAssess(BaseServerModel):
    """Pydantic model for `openassessmentblock.staff_assess` statement.

    The server emits this statement when a course team member submits an assessment
    of a learner's response.

    Attributes:
        event (dict): See ORAStaffAssessEventField.
        event_type (str): Consists of the value `openassessmentblock.staff_assess`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.staff_assess"
    )

    event: ORAStaffAssessEventField
    event_type: Literal["openassessmentblock.staff_assess"]
    page: Literal["x_module"]


class ORASubmitFeedbackOnAssessments(BaseServerModel):
    """Pydantic model for `openassessmentblock.submit_feedback_on_assessments`
    statement.

    The server emits this statement when a learner submits a suggestion, opinion or
    other feedback about the assessment process.

    Attributes:
        event (dict): See ORASubmitFeedbackOnAssessmentsEventField.
        event_type (str): Consists of the value
            `openassessmentblock.submit_feedback_on_assessments`.
        page (str): Consists of the value `x_module`.
    """  # noqa: D205

    __selector__ = selector(
        event_source="server",
        event_type="openassessmentblock.submit_feedback_on_assessments",
    )

    event: ORASubmitFeedbackOnAssessmentsEventField
    event_type: Literal["openassessmentblock.submit_feedback_on_assessments"]
    page: Literal["x_module"]


class ORACreateSubmission(BaseServerModel):
    """Pydantic model for `openassessmentblock.create_submission` statement.

    The server emits this statement when a learner submits a response, a peer
    assessment or a self assessment.

    Attributes:
        event (dict): See ORACreateSubmissionEventField.
        event_type (str): Consists of the value `openassessmentblock.create_submission`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.create_submission"
    )

    event: ORACreateSubmissionEventField
    event_type: Literal["openassessmentblock.create_submission"]
    page: Literal["x_module"]


class ORASaveSubmission(BaseServerModel):
    """Pydantic model for `openassessmentblock.save_submission` statement.

    The server emits this statement when the user clicks on the
    <kbd>Save your progress</kbd> button to save the current state of the
    response to an open assessment question.

    Attributes:
        event (str): See ORASaveSubmissionEventField.
        event_type (str): Consists of the value `openassessmentblock.save_submission`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server", event_type="openassessmentblock.save_submission"
    )

    event: ORASaveSubmissionEventField
    event_type: Literal["openassessmentblock.save_submission"]
    page: Literal["x_module"]


class ORAStudentTrainingAssessExample(BaseServerModel):
    """Pydantic model for `openassessment.student_training_assess_example` statement.

    The server emits this event when a learner submits an assessment for an example
    response within a training step.

    Attributes:
        event (dict): See ORAStudentTrainingAssessExampleEventField.
        event_type (str): Consists of the value
            `openassessment.student_training_assess_example`.
        page (str): Consists of the value `x_module`.
    """

    __selector__ = selector(
        event_source="server",
        event_type="openassessment.student_training_assess_example",
    )

    event: ORAStudentTrainingAssessExampleEventField
    event_type: Literal["openassessment.student_training_assess_example"]
    page: Literal["x_module"]


class ORAUploadFile(BaseBrowserModel):
    """Pydantic model for `openassessment.upload_file` statement.

    The browser emits this statement when a learner successfully uploads an image,
    .pdf, or other file as part of a response.

    Attributes:
        event (dict): See ORAUploadFileEventField.
        event_type (str): Consists of the value `openassessment.upload_file`.
        name (str): Consists of the value `openassessment.upload_file`.
    """

    __selector__ = selector(
        event_source="browser", event_type="openassessment.upload_file"
    )

    event: Union[Json[ORAUploadFileEventField], ORAUploadFileEventField]
    event_type: Literal["openassessment.upload_file"]
    name: Literal["openassessment.upload_file"]
