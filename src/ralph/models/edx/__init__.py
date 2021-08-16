"""edX pydantic models"""

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
