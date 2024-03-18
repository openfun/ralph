"""Cohort event field definition."""

import sys
from uuid import UUID

from pydantic import AnyHttpUrl, constr

from ...base import AbstractBaseEventField

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class CertificateBaseEventField(AbstractBaseEventField):
    """Pydantic model for cohort core `event` field.

    Attributes:
        certificate_id (uuid): Consists of the uuid of the generated certificate.
        certificate_url (url): Consists of the URL for the certificate web page.
        course_id (str): Consists of the ID of the course for which this
            certificate is issued.
        enrollment_mode (str): Consists of the course enrollment mode associated
            with this certificate.
        user_id (int): Consists of the numeric ID of the learner who earned this
            certificate.

    """

    certificate_id: UUID
    certificate_url: AnyHttpUrl
    course_id: constr(regex=r"^$|^course-v1:.+\+.+\+.+$")
    enrollment_mode: Literal["audit", "honor", "professional", "verified"]
    user_id: int


class EdxCertificateCreatedEventField(CertificateBaseEventField):
    """Pydantic model for `edx.certificate.created` `event` field.

    Attributes:
        generation_mode (str): Set to `batch` whent the certificate is generated
            automatically or `self` when a learner generated their own
            certificate.
    """

    generation_mode: Literal["batch", "self"]


class EdxCertificateRevokedEventField(CertificateBaseEventField):
    """Pydantic model for `edx.certificate.revoked` `event` field.

    Attributes:
        source (str): Consists of the source requesting revocation of
            the course certificate.
    """

    source: str


class EdxCertificateSharedEventField(CertificateBaseEventField):
    """Pydantic model for `edx.certificate.shared` `event` field.

    Attributes:
        social_network (str): Consists of the social network to which the
            certificate is shared.
    """

    social_network: str


class EdxCertificateEvidenceVisitedEventField(CertificateBaseEventField):
    """Pydantic model for `edx.certificate.evidence_visited` `event` field.

    Attributes:
        social_network (str): Consists of the social network to which the
            certificate is shared.
        source_url (str): Consists of the URL of the web site where the
            certificate evidence link was selected
    """

    social_network: str
    source_url: AnyHttpUrl


class CertificateGenerationBaseEventField(AbstractBaseEventField):
    """Pydantic model for certification generation core `event` field.

    Attributes:
        course_id (str): Consists of the ID of the course for which this
            certificate is issued.
    """

    course_id: constr(regex=r"^$|^course-v1:.+\+.+\+.+$")
