"""Enrollment event xAPI Converter."""

from typing import Set

from ralph.models.converter import ConversionItem
from ralph.models.edx.enrollment.statements import (
    EdxCourseEnrollmentActivated,
    EdxCourseEnrollmentDeactivated,
)
from ralph.models.xapi.lms.statements import LMSRegisteredCourse, LMSUnregisteredCourse

from .base import BaseXapiConverter


class LMSBaseXapiConverter(BaseXapiConverter):
    """Base LMS xAPI Converter."""

    def _get_conversion_items(self) -> Set[ConversionItem]:
        """Return a set of ConversionItems used for conversion."""
        conversion_items = super()._get_conversion_items()
        return conversion_items.union(
            {
                ConversionItem(
                    "object__id",
                    "event__course_id",
                    lambda course_id: f"{self.platform_url}/courses/{course_id}/info",
                ),
                ConversionItem(
                    "context__contextActivities__category",
                    None,
                    lambda _: [{"id": "https://w3id.org/xapi/lms"}],
                ),
            },
        )


class EdxCourseEnrollmentActivatedToLMSRegisteredCourse(LMSBaseXapiConverter):
    """Convert a common edX `edx.course.enrollment.activated` event to xAPI."""

    __src__ = EdxCourseEnrollmentActivated
    __dest__ = LMSRegisteredCourse


class EdxCourseEnrollmentDeactivatedToLMSUnregisteredCourse(LMSBaseXapiConverter):
    """Convert a common edX `edx.course.enrollment.deactivated` event to xAPI."""

    __src__ = EdxCourseEnrollmentDeactivated
    __dest__ = LMSUnregisteredCourse
