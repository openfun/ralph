"""Tests for peer instruction models event fields."""

import json
import re

import pytest
from pydantic.error_wrappers import ValidationError

from ralph.models.edx.certificate.fields.events import (
    CertificateBaseEventField,
    CertificateGenerationBaseEventField,
    EdxCertificateCreatedEventField,
)

from tests.factories import mock_instance


def test_models_edx_certificate_base_event_field_with_valid_field():
    """Test that a valid `CertificateBaseEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(CertificateBaseEventField)
    assert re.match(r"^$|^course-v1:.+\+.+\+.+$", field.course_id)
    assert field.enrollment_mode in ("audit", "honor", "professional", "verified")


@pytest.mark.parametrize(
    "enrollment_mode",
    ["audi", "onor", "professionnal", "verify"],
)
def test_models_edx_certificate_base_event_field_with_invalid_enrollment_mode_value(
    enrollment_mode,
):
    """Test that an invalid `enrollment_mode` value in
    `CertificateBaseEventField` raises a `ValidationError`.
    """
    subfield = mock_instance(CertificateBaseEventField)
    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["enrollment_mode"] = enrollment_mode

    with pytest.raises(ValidationError, match="enrollment_mode"):
        CertificateBaseEventField(**invalid_subfield)


@pytest.mark.parametrize(
    "course_id",
    [
        "course-v1:+course+not_empty",
        "course-v1:org",
        "course-v1:org+course",
        "course-v1:org+course+",
    ],
)
def test_models_edx_certificate_base_event_field_with_invalid_course_id_value(
    course_id,
):
    """Test that an invalid `CertificateBaseEventField` statement raises a
    `ValidationError`.
    """
    statement = mock_instance(CertificateBaseEventField)
    invalid_statement = json.loads(statement.json())
    invalid_statement["course_id"] = course_id

    with pytest.raises(
        ValidationError, match="course_id\n  String should match pattern"
    ):
        CertificateBaseEventField(**invalid_statement)


def test_models_edx_edx_certificate_created_event_field_with_valid_field():
    """Test that a valid `EdxCertificateCreatedEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(EdxCertificateCreatedEventField)

    assert field.generation_mode in ("batch", "self")


@pytest.mark.parametrize(
    "generation_mode",
    ["batched", "shelf"],
)
def test_models_edx_edx_certificate_created_event_field_with_invalid_generation_mode_value(  # noqa:E501
    generation_mode,
):
    """Test that an invalid `enrollment_mode` value in
    `EdxCertificateCreatedEventField` raises a `ValidationError`.
    """
    subfield = mock_instance(EdxCertificateCreatedEventField)
    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["generation_mode"] = generation_mode

    with pytest.raises(ValidationError, match="generation_mod"):
        EdxCertificateCreatedEventField(**invalid_subfield)


def test_models_edx_certificate_generation_base_event_field_with_valid_field():
    """Test that a valid `CertificateGenerationBaseEventField` does not raise a
    `ValidationError`.
    """
    field = mock_instance(CertificateGenerationBaseEventField)
    assert re.match(r"^$|^course-v1:.+\+.+\+.+$", field.course_id)


@pytest.mark.parametrize(
    "course_id",
    [
        "course-v1:+course+not_empty",
        "course-v1:org",
        "course-v1:org+course",
        "course-v1:org+course+",
    ],
)
def test_models_edx_certificate_generation_base_event_field_with_invalid_course_id_value(  # noqa: E501
    course_id,
):
    """Test that an invalid `CertificateGenerationBaseEventField` statement raises a
    `ValidationError`.
    """
    statement = mock_instance(CertificateGenerationBaseEventField)
    invalid_statement = json.loads(statement.json())
    invalid_statement["course_id"] = course_id

    with pytest.raises(
        ValidationError, match="course_id\n  String should match pattern"
    ):
        CertificateGenerationBaseEventField(**invalid_statement)
