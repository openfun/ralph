"""Tests for the xAPI open response assessment statements"""

import json

from hypothesis import given, provisional, settings
from hypothesis import strategies as st

from ralph.models.selector import ModelSelector
from ralph.models.xapi.constants import EXTENSION_RESPONSES_ID
from ralph.models.xapi.fields.actors import ActorAccountField, ActorField
from ralph.models.xapi.fields.verbs import SavedVerbField
from ralph.models.xapi.open_response_assessment.fields.objects import (
    QuestionObjectDefinitionField,
    QuestionObjectField,
)
from ralph.models.xapi.open_response_assessment.fields.results import (
    QuestionSavedResultExtensionsField,
    QuestionSavedResultField,
)
from ralph.models.xapi.open_response_assessment.statements import QuestionSaved


@settings(max_examples=1)
@given(
    st.builds(
        QuestionSaved,
        actor=st.builds(
            ActorField,
            account=st.builds(
                ActorAccountField, name=st.just("username"), homePage=provisional.urls()
            ),
        ),
        object=st.builds(
            QuestionObjectField,
            definition=st.builds(QuestionObjectDefinitionField),
            id=provisional.urls(),
        ),
        verb=st.builds(SavedVerbField),
        result=st.builds(
            QuestionSavedResultField,
            extensions=st.builds(
                QuestionSavedResultExtensionsField,
                **{EXTENSION_RESPONSES_ID: st.just(["first", "second"])}
            ),
        ),
    )
)
def test_models_xapi_ora_question_saved_selector_with_valid_statement(statement):
    """Tests given a `QuestionSaved` statement, the `get_model` method should return
    a `QuestionSaved` model."""

    assert statement.verb.id == "https://w3id.org/xapi/dod-isd/verbs/saved"
    statement = json.loads(statement.json())
    assert (
        ModelSelector(module="ralph.models.xapi").get_model(statement) is QuestionSaved
    )
