"""Tests for the open response assessment event models"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.edx.problem import DemandhintDisplayed, DemandhintDisplayedEventField
from ralph.models.edx.x_block import ContextField
from ralph.models.selector import ModelSelector


@settings(max_examples=1)
@given(
    st.builds(
        DemandhintDisplayed,
        context=st.builds(ContextField),
        referer=provisional.urls(),
        event=st.builds(DemandhintDisplayedEventField),
    )
)
def test_models_edx_demandhint_displayed_with_valid_event(event):
    """Tests given an `edx.problem.hint.demandhint_displayed` event the get_model method
    should return an DemandhintDisplayed model.
    """

    event = json.loads(event.json())
    assert (
        ModelSelector(module="ralph.models.edx").get_model(event) is DemandhintDisplayed
    )
