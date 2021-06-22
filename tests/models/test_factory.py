"""Tests for the hypothesis_model_factory"""

import json

import pytest
from pydantic import ValidationError
from ralph.models.generator import hypothesis_model_factory

from ralph.models.selector import ModelSelector

@pytest.mark.parametrize(
    "model_class",
    list(ModelSelector(module="ralph.models.edx").model_rules.keys())
    + list(ModelSelector(module="ralph.models.xapi").model_rules.keys()),
)
def test_factory(model_class):
    """Tests the hypothesis_model_factory."""

    try:
        model = hypothesis_model_factory(model_class)
        model_class(**json.loads(model.json(by_alias=True)))
    except ValidationError as err:
        raise pytest.fail(f"Factory failed for model: {model_class}") from err
