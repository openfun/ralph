"""Open Response Assessment events model event fields definitions."""

from datetime import datetime
from typing import Dict, List, Optional, Union

try:
    from typing import Annotated, iteral
except ImportError:
    from typing_extensions import Annotated, Literal

from uuid import UUID

from pydantic import StringConstraints

from ralph.models.edx.base import AbstractBaseEventField, BaseModelWithConfig


class ORAGetPeerSubmissionEventField(AbstractBaseEventField):
    """Pydantic model for `openassessmentblock.get_peer_submission`.`event` field.

    Attributes:
        course_id (str): Consists of the course identifier including the assessment.
        item_id (str): Consists of the locator string that identifies the problem in
            the course.
        requesting_student_id (str): Consists of the course-specific anonymized user ID
            of the learner who retrieved the response for peer assessment.
        submission_returned_uuid (str): Consists of the unique identifier of the
            response that was retrieved for assessment. Set to `None` if no assessment
            available.
    """

    course_id: Annotated[str, StringConstraints(max_length=255)]
    item_id: Annotated[str, StringConstraints(
        pattern=(
            r"^block-v1:.+\+.+\+.+type@openassessment"  # noqa : F722
            r"+block@[a-f0-9]{32}$"  # noqa : F722
        )
    )]
    requesting_student_id: str
    submission_returned_uuid: Union[str, None] = None


class ORAGetSubmissionForStaffGradingEventField(AbstractBaseEventField):
    # noqa: D205, D415
    """Pydantic model for `openassessmentblock.get_submission_for_staff_grading`.
    `event` field.

    Attributes:
        item_id (str): Consists of the locator string that identifies the problem in
            the course.
        submission_returned_uuid (str): Consists of the unique identifier of the
            response that was retrieved for assessment. Set to `None` if no assessment
            available.
        requesting_staff_id (str): Consists of the course-specific anonymized user ID
            of the course team member who is retrieved the response for grading.
        type (str): Consists of the type of staff grading that is being performed.
            Currently set to `full-grade`.
    """

    item_id: Annotated[str, StringConstraints(
        pattern=(
            r"^block-v1:.+\+.+\+.+type@openassessment"  # noqa : F722
            r"+block@[a-f0-9]{32}$"  # noqa : F722
        )
    )]
    submission_returned_uuid: Union[str, None] = None
    requesting_staff_id: str
    type: Literal["full-grade"]


class ORAAssessEventPartsCriterionField(BaseModelWithConfig):
    """Pydantic model for assessement `event`.`parts`.`criterion` field.

    Attributes:
        name (str): Consists of the criterion name.
        points_possible (int): Consists of the maximum number of points
            allocated to the criterion.
    """

    name: str
    points_possible: int


class ORAAssessEventPartsField(BaseModelWithConfig):
    """Pydantic model for assessment `event`.`parts` field.

    Attributes:
        option (str): Consists of the option that the learner selected for it.
        criterion (dict): see ORAAssessEventPartsCriterionField.
        feedback (str): Consists of feedback comments that the learner could have
            supplied.
    """

    option: str
    criterion: ORAAssessEventPartsCriterionField
    feedback: Optional[str] = None


class ORAAssessEventRubricField(BaseModelWithConfig):
    """Pydantic model for assessment `event`.`rubric` field.

    This field is defined in:
    - `openassessmentblock.peer_assess`
    - `openassessmentblock.self_assess`
    - `openassessmentblock.staff_assess`

    Attributes:
        content_hash: Consists of the identifier of the rubric that the learner used to
            assess the response.
    """

    content_hash: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{1,40}$")]  # noqa: F722


class ORAAssessEventField(AbstractBaseEventField):
    """Pydantic model for assessment `event` field.

    This field is defined in:
        - `openassessmentblock.peer_assess`
        - `openassessmentblock.self_assess`
        - `openassessmentblock.staff_assess`

    Attributes:
        feedback (str): Consists of the learner's comments about the submitted response.
        parts (list): see ORAAssessEventPartsField.
        rubric (dict): see ORAPeerAssessEventRubricField.
        scored_at (datetime): Consists of the timestamp for when the assessment was
            submitted.
        scorer_id (str): Consists of the course-specific anonymized user ID of the
            learner who submitted the assessment.
        score_type (str): Consists of either `PE` value for a peer assessment, `SE` for
            a self assessment or `ST` for a staff assessment.
        submission_uuid (str): Consists of the unique identifier for the submitted
            response.
    """

    feedback: str
    parts: List[ORAAssessEventPartsField]
    rubric: ORAAssessEventRubricField
    scored_at: datetime
    scorer_id: Annotated[str, StringConstraints(max_length=40)]
    score_type: Literal["PE", "SE", "ST"]
    submission_uuid: UUID


class ORAStaffAssessEventField(ORAAssessEventField):
    """Pydantic model for `openassessmentblock.staff_assess`.`event` field.

    Attributes:
        type (str): Consists of the type of staff grading that is being performed. Can
            be either equalt to `regrade` in the case of a grade override or
            `full-grade` in the case of an included staff assessment step.
    """

    type: Literal["regrade", "full-grade"]


class ORASubmitFeedbackOnAssessmentsEventField(AbstractBaseEventField):
    # noqa: D205, D415
    """Pydantic model for `openassessmentblock.submit_feedback_on_assessments`.
    `event` field.

    Attributes:
        feedback_text (str): Consists of the learner's comments about the assessment
            process.
        options (list): Consists of the label of each checkbox option that the learner
            selected to evaluate the assessment process.
        submission_uuid (str): Consists of the unique identifier for for the feedback.
    """

    feedback_text: str
    options: List[str]
    submission_uuid: UUID


class ORACreateSubmissionEventAnswerField(BaseModelWithConfig):
    # noqa: D205, D415
    """Pydantic model for `openassessmentblock.create_submission`.`event`.`answer`
    field.

    Attributes:
        parts (dict): Consists of a key-value dictionary with all answers text.
        file_keys (list): Consists of a list of file identifiers if files are given for
            answer.
        files_description (list): Consists of a list of file descriptions if files are
            given for answer.
    """

    parts: List[Dict[Literal["text"], str]]
    file_keys: Optional[List[str]] = None
    files_descriptions: Optional[List[str]] = None


class ORACreateSubmissionEventField(AbstractBaseEventField):
    """Pydantic model for `openassessmentblock.create_submission`.`event` field.

    Attributes:
        answer (dict): see ORACreateSubmissionEventAnswerField.
        attempt_number (int): Consists of the number of submission attempts. Currently,
            this value is set to 1.
        created_at (datetime): Consists of the timestamp for when the learner submitted
            the response.
        submitted_at (datetime): Consists of the timestamp for when the learner
            submitted the response. This value is the same as `submitted_at`.
        submission_uuid (str): Consists of the unique identifier of the response.
    """

    answer: ORACreateSubmissionEventAnswerField
    attempt_number: int
    created_at: datetime
    submitted_at: datetime
    submission_uuid: UUID


class ORASaveSubmissionEventSavedResponseField(BaseModelWithConfig):
    """Pydantic model for `openassessmentblock.save_submission`.`saved_response` field.

    Attributes:
        text (str): Consists of the response text.
        file_upload_key (str): Consists of the AWS S3 key that identifies the location
            of the uploaded file on the Amazon S3 storage service. Only present when
            responses include an image, .pdf, or other file.
    """

    text: str
    file_upload_key: Optional[str] = None


class ORASaveSubmissionEventField(AbstractBaseEventField):
    """Pydantic model for `openassessmentblock.save_submission`.`event` field.

    Attributes:
        saved_response (str): Consists of a JSON string of the users saved responses.
            Note:
                Responses have a length limit of 100000 in the front-end but not in the
                back-end. Events are truncated at `TRACK_MAX_EVENT` which is 50000 by
                default. Also the `eventtracking.backends.logger.LoggerBackend`
                silently drops events when they exceed `TRACK_MAX_EVENT`.
    """

    # pylint: disable=unsubscriptable-object
    saved_response: ORASaveSubmissionEventSavedResponseField


class ORAStudentTrainingAssessExampleEventField(AbstractBaseEventField):
    # noqa: D205, D415
    """Pydantic model for `openassessment.student_training_assess_example`.`event`
    field.

    Attributes:
        corrections (dict): Consists of a set of name/value pairs that identify
            criteria for which the learner selected a different option than the course
            team.
        options_selected (dict): Consists of a set of name/value pairs that identify
            the option that the learner selected for each criterion in the rubric.
        submission_uuid (str): Consists of the unique identifier of the response.
    """

    corrections: Dict[str, str]
    options_selected: Dict[str, str]
    submission_uuid: UUID


class ORAUploadFileEventField(BaseModelWithConfig):
    """Pydantic model for `openassessment.upload_file`.`event` field.

    Attributes:
        fileName (str): Consists of the name of the uploaded file.
        fileSize (int): Consists of the bytes size of the uploaded file.
        fileType (str): Consists of the MIME type of the uploaded file.
    """

    fileName: Annotated[str, StringConstraints(max_length=255)]
    fileSize: int
    fileType: str
