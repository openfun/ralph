"""edX pydantic models."""

# flake8: noqa

from ralph.models.edx.navigational import statements

from .enrollment.statements import (
    EdxCourseEnrollmentActivated,
    EdxCourseEnrollmentDeactivated,
    EdxCourseEnrollmentModeChanged,
    EdxCourseEnrollmentUpgradeSucceeded,
    UIEdxCourseEnrollmentUpgradeClicked,
)
from .navigational.statements import UIPageClose, UISeqGoto, UISeqNext, UISeqPrev
from .open_response_assessment.statements import (
    ORACreateSubmission,
    ORAGetPeerSubmission,
    ORAGetSubmissionForStaffGrading,
    ORAPeerAssess,
    ORASaveSubmission,
    ORASelfAssess,
    ORAStaffAssess,
    ORAStudentTrainingAssessExample,
    ORASubmitFeedbackOnAssessments,
    ORAUploadFile,
)
from .problem_interaction.statements import (
    EdxProblemHintDemandhintDisplayed,
    EdxProblemHintFeedbackDisplayed,
    ProblemCheck,
    ProblemCheckFail,
    ProblemRescore,
    ProblemRescoreFail,
    ResetProblem,
    ResetProblemFail,
    SaveProblemFail,
    SaveProblemSuccess,
    ShowAnswer,
    UIProblemCheck,
    UIProblemGraded,
    UIProblemReset,
    UIProblemSave,
    UIProblemShow,
)
from .server import Server
from .textbook_interaction.statements import (
    UIBook,
    UITextbookPdfChapterNavigated,
    UITextbookPdfDisplayScaled,
    UITextbookPdfOutlineToggled,
    UITextbookPdfPageNavigated,
    UITextbookPdfPageScrolled,
    UITextbookPdfSearchCaseSensitivityToggled,
    UITextbookPdfSearchExecuted,
    UITextbookPdfSearchHighlightToggled,
    UITextbookPdfSearchNavigatedNext,
    UITextbookPdfThumbnailNavigated,
    UITextbookPdfThumbnailsToggled,
    UITextbookPdfZoomButtonsChanged,
    UITextbookPdfZoomMenuChanged,
)
from .video.statements import (
    UIHideTranscript,
    UILoadVideo,
    UIPauseVideo,
    UIPlayVideo,
    UISeekVideo,
    UIShowTranscript,
    UISpeedChangeVideo,
    UIStopVideo,
    UIVideoHideCCMenu,
    UIVideoShowCCMenu,
)
