"""Tests for the models selector"""

import json

import pytest
from pydantic.main import BaseModel

from ralph.exceptions import ModelRulesException, UnknownEventException
from ralph.models.edx.navigational import PageCloseBrowserEventModel
from ralph.models.edx.server import ServerEventModel
from ralph.models.selector import (
    LazyModelField,
    ModelRules,
    ModelSelector,
    Rule,
    selector,
)

from tests.fixtures.edx.navigational import PageCloseBrowserEventFactory
from tests.fixtures.edx.server import ServerEventFactory


@pytest.mark.parametrize(
    "model_rules,decision_tree",
    [
        # Empty model_rules => empty decision_tree.
        ({}, {}),
        # Single model, single rule case.
        (
            {ServerEventModel: selector(event_source="server")},
            {
                Rule(LazyModelField("event_source"), "server"): {
                    True: ServerEventModel,
                    False: None,
                }
            },
        ),
        # Single model, multiple rules case.
        (
            {
                ServerEventModel: selector(
                    event_source="server", event_type=LazyModelField("context__path")
                )
            },
            {
                Rule(LazyModelField("event_source"), "server"): {
                    True: {
                        Rule(
                            LazyModelField("event_type"),
                            LazyModelField("context__path"),
                        ): {
                            True: ServerEventModel,
                            False: None,
                        },
                    },
                    False: None,
                }
            },
        ),
        # Two models, multiple rules case, each rule occurs only once.
        (
            {
                PageCloseBrowserEventModel: selector(
                    event_source="browser", event_type="page_close"
                ),
                ServerEventModel: selector(
                    event_source="server", event_type=LazyModelField("context__path")
                ),
            },
            {
                Rule(LazyModelField("event_source"), "browser"): {
                    True: {
                        Rule(LazyModelField("event_type"), "page_close"): {
                            True: PageCloseBrowserEventModel,
                            False: None,
                        }
                    },
                    False: {
                        Rule(LazyModelField("event_source"), "server"): {
                            True: {
                                Rule(
                                    LazyModelField("event_type"),
                                    LazyModelField("context__path"),
                                ): {
                                    True: ServerEventModel,
                                    False: None,
                                }
                            },
                            False: None,
                        }
                    },
                }
            },
        ),
        # Tree models, multiple rules, event_source="server" occurs twice.
        (
            {
                PageCloseBrowserEventModel: selector(
                    event_source="browser", event_type="page_close"
                ),
                ServerEventModel: selector(
                    event_source="server", event_type=LazyModelField("context__path")
                ),
                BaseModel: selector(event_source="server", event_type="base"),
            },
            {
                Rule(LazyModelField("event_source"), "server"): {
                    True: {
                        Rule(
                            LazyModelField("event_type"),
                            LazyModelField("context__path"),
                        ): {
                            True: ServerEventModel,
                            False: {
                                Rule(LazyModelField("event_type"), "base"): {
                                    True: BaseModel,
                                    False: None,
                                }
                            },
                        }
                    },
                    False: {
                        Rule(LazyModelField("event_source"), "browser"): {
                            True: {
                                Rule(LazyModelField("event_type"), "page_close"): {
                                    True: PageCloseBrowserEventModel,
                                    False: None,
                                }
                            },
                            False: None,
                        }
                    },
                }
            },
        ),
    ],
)
def test_models_selector_model_selector_decision_tree(model_rules, decision_tree):
    """Given `model_rules` the ModelSelector should create the expected decision tree."""

    model_selector = ModelSelector(module="ralph.models.edx")
    assert model_selector.get_decision_tree(model_rules) == decision_tree


@pytest.mark.parametrize(
    "model_rules,rules",
    [
        # rules are equal to ServerEventModel rules.
        ({ServerEventModel: selector(foo="foo")}, selector(foo="foo")),
        # rules are a subset of ServerEventModel rules.
        ({ServerEventModel: selector(foo="foo", bar="bar")}, selector(bar="bar")),
        # rules are a superset of ServerEventModel rules.
        ({ServerEventModel: selector(bar="bar")}, selector(foo="foo", bar="bar")),
    ],
)
def test_models_selector_model_selector_model_rules(model_rules, rules):
    """Check that the ModelRules dictionary raises an exception when the provided
    model has a list of rules that is a superset or subset of another list of rules.
    """

    model_rules = ModelRules(model_rules)
    with pytest.raises(ModelRulesException):
        model_rules[BaseModel] = rules


@pytest.mark.parametrize(
    "event,model",
    [
        (ServerEventFactory(), ServerEventModel),
        (PageCloseBrowserEventFactory(), PageCloseBrowserEventModel),
    ],
)
def test_models_selector_model_selector_get_model_with_valid_event(event, model):
    """Tests given a valid event the get_model method should return the corresponding model."""

    event = json.loads(event.json())
    assert ModelSelector(module="ralph.models.edx").get_model(event) is model


@pytest.mark.parametrize("event", [{"invalid": "event"}])
def test_models_selector_model_selector_get_model_with_invalid_event(event):
    """Tests given an invalid event the get_model method should raise UnknownEventException."""

    with pytest.raises(UnknownEventException):
        ModelSelector(module="ralph.models.edx").get_model(event)


@pytest.mark.parametrize(
    "module,model_rules",
    [
        (type("empty_module", (), {}), {}),
        (type("no_classes", (), {"int_member": 1, "str_member": "foo"}), {}),
        (
            type("not_a_subclass_of_base_model", (), {"not_base_model": ModelRules}),
            {},
        ),
        (
            type("missing_selector_attribute", (), {"no_selector": BaseModel}),
            {},
        ),
        (
            type(
                "one_valid_base_model", (), {"page_close": PageCloseBrowserEventModel}
            ),
            {PageCloseBrowserEventModel: PageCloseBrowserEventModel.__selector__},
        ),
        (
            type(
                "two_valid_base_models_and_other_members_to_ignore",
                (),
                {
                    "int_member": 1,
                    "page_close": PageCloseBrowserEventModel,
                    "no_selector": BaseModel,
                    "not_base_model": ModelRules,
                    "server": ServerEventModel,
                    "str_member": "foo",
                },
            ),
            {
                PageCloseBrowserEventModel: PageCloseBrowserEventModel.__selector__,
                ServerEventModel: ServerEventModel.__selector__,
            },
        ),
    ],
)
def test_models_selector_model_selector_build_model_rules(module, model_rules):
    """Given an imported module build_model_rules should return the corresponding model_rules."""

    assert ModelSelector.build_model_rules(module) == model_rules
