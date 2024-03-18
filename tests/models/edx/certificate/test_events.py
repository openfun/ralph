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

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(CertificateBaseEventField)
def test_models_edx_certificate_base_event_field_with_valid_field(field):
    """Test that a valid `CertificateBaseEventField` does not raise a
    `ValidationError`.
    """
    assert re.match(r"^$|^course-v1:.+\+.+\+.+$", field.course_id)
    assert field.enrollment_mode in ("audit", "honor", "professional", "verified")


@pytest.mark.parametrize(
    "enrollment_mode",
    ["audi", "onor", "professionnal", "verify"],
)
@custom_given(CertificateBaseEventField)
def test_models_edx_certificate_base_event_field_with_invalid_enrollment_mode_value(
    enrollment_mode, subfield
):
    """Test that an invalid `enrollment_mode` value in
    `CertificateBaseEventField` raises a `ValidationError`.
    """
    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["enrollment_mode"] = enrollment_mode

    with pytest.raises(ValidationError, match="enrollment_mode\n  unexpected value"):
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
@custom_given(CertificateBaseEventField)
def test_models_edx_certificate_base_event_field_with_invalid_course_id_value(
    course_id, statement
):
    """Test that an invalid `CertificateBaseEventField` statement raises a
    `ValidationError`.
    """
    invalid_statement = json.loads(statement.json())
    invalid_statement["course_id"] = course_id

    with pytest.raises(
        ValidationError, match="course_id\n  string does not match regex"
    ):
        CertificateBaseEventField(**invalid_statement)


@custom_given(EdxCertificateCreatedEventField)
def test_models_edx_edx_certificate_created_event_field_with_valid_field(field):
    """Test that a valid `EdxCertificateCreatedEventField` does not raise a
    `ValidationError`.
    """

    assert field.generation_mode in ("batch", "self")


@pytest.mark.parametrize(
    "generation_mode",
    ["batched", "shelf"],
)
@custom_given(EdxCertificateCreatedEventField)
def test_models_edx_edx_certificate_created_event_field_with_invalid_generation_mode_value(  # noqa:E501
    generation_mode, subfield
):
    """Test that an invalid `enrollment_mode` value in
    `EdxCertificateCreatedEventField` raises a `ValidationError`.
    """
    invalid_subfield = json.loads(subfield.json())
    invalid_subfield["generation_mode"] = generation_mode

    with pytest.raises(ValidationError, match="generation_mode\n  unexpected value"):
        EdxCertificateCreatedEventField(**invalid_subfield)


@custom_given(CertificateGenerationBaseEventField)
def test_models_edx_certificate_generation_base_event_field_with_valid_field(field):
    """Test that a valid `CertificateGenerationBaseEventField` does not raise a
    `ValidationError`.
    """
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
@custom_given(CertificateGenerationBaseEventField)
def test_models_edx_certificate_generation_base_event_field_with_invalid_course_id_value(  # noqa: E501
    course_id, statement
):
    """Test that an invalid `CertificateGenerationBaseEventField` statement raises a
    `ValidationError`.
    """
    invalid_statement = json.loads(statement.json())
    invalid_statement["course_id"] = course_id

    with pytest.raises(
        ValidationError, match="course_id\n  string does not match regex"
    ):
        CertificateGenerationBaseEventField(**invalid_statement)
