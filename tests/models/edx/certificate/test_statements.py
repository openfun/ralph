"""Tests for the peer_instruction event models."""

import json

import pytest

from ralph.models.edx.certificate.statements import (
    EdxCertificateCreated,
    EdxCertificateEvidenceVisited,
    EdxCertificateGenerationDisabled,
    EdxCertificateGenerationEnabled,
    EdxCertificateRevoked,
    EdxCertificateShared,
)
from ralph.models.selector import ModelSelector

from tests.factories import mock_instance


@pytest.mark.parametrize(
    "class_",
    [
        EdxCertificateCreated,
        EdxCertificateEvidenceVisited,
        EdxCertificateGenerationDisabled,
        EdxCertificateGenerationEnabled,
        EdxCertificateRevoked,
        EdxCertificateShared,
    ],
)
def test_models_edx_certificate_selectors_with_valid_statements(class_):
    """Test given a valid certificate edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(mock_instance(class_).model_dump_json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


def test_models_edx_edx_certificate_created_with_valid_statement():
    """Test that a `edx.certificate.created` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCertificateCreated)
    assert statement.event_type == "edx.certificate.created"
    assert statement.name == "edx.certificate.created"


def test_models_edx_edx_certificate_evidence_visited_with_valid_statement():
    """Test that a `eedx.certificate.evidence_visited` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCertificateEvidenceVisited)
    assert statement.event_type == "edx.certificate.evidence_visited"
    assert statement.name == "edx.certificate.evidence_visited"


def test_models_edx_edx_certificate_generation_disabled_with_valid_statement():
    """Test that a `edx.certificate.generation.disabled` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCertificateGenerationDisabled)
    assert statement.event_type == "edx.certificate.generation.disabled"
    assert statement.name == "edx.certificate.generation.disabled"


def test_models_edx_edx_certificate_generation_enabled_with_valid_statement():
    """Test that a `edx.certificate.generation.enabled` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCertificateGenerationEnabled)
    assert statement.event_type == "edx.certificate.generation.enabled"
    assert statement.name == "edx.certificate.generation.enabled"


def test_models_edx_edx_certificate_revoked_with_valid_statement():
    """Test that a `edx.certificate.revoked` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCertificateRevoked)
    assert statement.event_type == "edx.certificate.revoked"
    assert statement.name == "edx.certificate.revoked"


def test_models_edx_edx_certificate_shared_with_valid_statement():
    """Test that a `edx.certificate.shared` statement has the expected
    `event_type` and `name`.
    """
    statement = mock_instance(EdxCertificateShared)
    assert statement.event_type == "edx.certificate.shared"
    assert statement.name == "edx.certificate.shared"
