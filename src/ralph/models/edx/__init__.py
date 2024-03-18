"""edX pydantic models."""

# flake8: noqa

from ralph.models.edx.navigational import statements

from .bookmark.statements import (
    EdxBookmarkRemoved,
    EdxBookmarkAdded,
    EdxBookmarkListed,
    UIEdxBookmarkAccessed,
    UIEdxCourseToolAccessed,
)
from .certificate.statements import (
    EdxCertificateCreated,
    EdxCertificateEvidenceVisited,
    EdxCertificateGenerationDisabled,
    EdxCertificateGenerationEnabled,
    EdxCertificateRevoked,
    EdxCertificateShared,
)
from .cohort.statements import (
    EdxCohortCreated,
    EdxCohortUserAdded,
    EdxCohortUserRemoved,
)
from .content_library_interaction.statements import (
    EdxLibraryContentBlockContentAssigned,
    EdxLibraryContentBlockContentRemoved,
)
from .course_content_completion.statements import UIEdxDoneToggled, EdxDoneToggled
from .drag_and_drop.statements import (
    EdxDragAndDropV2FeedbackClosed,
    EdxDragAndDropV2FeedbackOpened,
    EdxDragAndDropV2ItemDropped,
    EdxDragAndDropV2ItemPickedUp,
    EdxDragAndDropV2Loaded,
)
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
from .poll.statements import XBlockPollSubmitted, XBlockPollViewResults
from .peer_instruction.statements import (
    PeerInstructionAccessed,
    PeerInstructionOriginalSubmitted,
    PeerInstructionRevisedSubmitted,
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
from .survey.statements import XBlockSurveySubmitted, XBlockSurveyViewResults
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
