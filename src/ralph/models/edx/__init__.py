"""edX pydantic models"""

# flake8: noqa

from .enrollment import (
    EdxCourseEnrollmentActivated,
    EdxCourseEnrollmentDeactivated,
    EdxCourseEnrollmentModeChanged,
    EdxCourseEnrollmentUpgradeSucceeded,
    UIEdxCourseEnrollmentUpgradeClicked,
)
from .navigational import UIPageClose, UISeqGoto, UISeqNext, UISeqPrev
from .server import ServerEvent
