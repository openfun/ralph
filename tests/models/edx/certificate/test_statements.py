"""Tests for the peer_instruction event models."""

import json

import pytest
from hypothesis import strategies as st

from ralph.models.edx.certificate.statements import (
    EdxCertificateCreated,
    EdxCertificateEvidenceVisited,
    EdxCertificateGenerationDisabled,
    EdxCertificateGenerationEnabled,
    EdxCertificateRevoked,
    EdxCertificateShared,
)
from ralph.models.selector import ModelSelector

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


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
@custom_given(st.data())
def test_models_edx_certificate_selectors_with_valid_statements(class_, data):
    """Test given a valid certificate edX statement the `get_first_model`
    selector method should return the expected model.
    """
    statement = json.loads(data.draw(custom_builds(class_)).json())
    model = ModelSelector(module="ralph.models.edx").get_first_model(statement)
    assert model is class_


@custom_given(EdxCertificateCreated)
def test_models_edx_edx_certificate_created_with_valid_statement(
    statement,
):
    """Test that a `edx.certificate.created` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.certificate.created"
    assert statement.name == "edx.certificate.created"


@custom_given(EdxCertificateEvidenceVisited)
def test_models_edx_edx_certificate_evidence_visited_with_valid_statement(
    statement,
):
    """Test that a `eedx.certificate.evidence_visited` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.certificate.evidence_visited"
    assert statement.name == "edx.certificate.evidence_visited"


@custom_given(EdxCertificateGenerationDisabled)
def test_models_edx_edx_certificate_generation_disabled_with_valid_statement(
    statement,
):
    """Test that a `edx.certificate.generation.disabled` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.certificate.generation.disabled"
    assert statement.name == "edx.certificate.generation.disabled"


@custom_given(EdxCertificateGenerationEnabled)
def test_models_edx_edx_certificate_generation_enabled_with_valid_statement(
    statement,
):
    """Test that a `edx.certificate.generation.enabled` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.certificate.generation.enabled"
    assert statement.name == "edx.certificate.generation.enabled"


@custom_given(EdxCertificateRevoked)
def test_models_edx_edx_certificate_revoked_with_valid_statement(
    statement,
):
    """Test that a `edx.certificate.revoked` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.certificate.revoked"
    assert statement.name == "edx.certificate.revoked"


@custom_given(EdxCertificateShared)
def test_models_edx_edx_certificate_shared_with_valid_statement(
    statement,
):
    """Test that a `edx.certificate.shared` statement has the expected
    `event_type` and `name`.
    """
    assert statement.event_type == "edx.certificate.shared"
    assert statement.name == "edx.certificate.shared"
