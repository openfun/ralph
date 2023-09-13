"""Tests for the models selector."""


import pytest
from pydantic import BaseModel

from ralph.exceptions import UnknownEventException
from ralph.models.edx.navigational.statements import UIPageClose, UISeqGoto
from ralph.models.edx.server import Server
from ralph.models.selector import LazyModelField, ModelSelector, Rule, selector


@pytest.mark.parametrize(
    "model_rules,decision_tree",
    [
        # Empty model_rules => empty decision_tree.
        ({}, []),
        # Single model, single rule case.
        (
            {
                Server: selector(  # pylint: disable=unhashable-member
                    event_source="server"
                )
            },
            {
                Rule(LazyModelField("event_source"), "server"): {
                    True: [Server],
                    False: None,
                }
            },
        ),
        # Single model, multiple rules case.
        (
            {
                Server: selector(  # pylint: disable=unhashable-member
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
                            True: [Server],
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
                UIPageClose: selector(  # pylint: disable=unhashable-member
                    event_source="browser", event_type="page_close"
                ),
                Server: selector(  # pylint: disable=unhashable-member
                    event_source="server", event_type=LazyModelField("context__path")
                ),
            },
            {
                Rule(LazyModelField("event_source"), "browser"): {
                    True: {
                        Rule(LazyModelField("event_type"), "page_close"): {
                            True: [UIPageClose],
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
                                    True: [Server],
                                    False: None,
                                }
                            },
                            False: None,
                        }
                    },
                }
            },
        ),
        # Three models, multiple rules, event_source="server" occurs twice.
        (
            {
                UIPageClose: selector(  # pylint: disable=unhashable-member
                    event_source="browser", event_type="page_close"
                ),
                Server: selector(  # pylint: disable=unhashable-member
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
                            True: [Server],
                            False: {
                                Rule(LazyModelField("event_type"), "base"): {
                                    True: [BaseModel],
                                    False: None,
                                }
                            },
                        }
                    },
                    False: {
                        Rule(LazyModelField("event_source"), "browser"): {
                            True: {
                                Rule(LazyModelField("event_type"), "page_close"): {
                                    True: [UIPageClose],
                                    False: None,
                                }
                            },
                            False: None,
                        }
                    },
                }
            },
        ),
        # Three models, multiple rules, two models have the same rules.
        (
            {
                UIPageClose: selector(  # pylint: disable=unhashable-member
                    event_source="browser", event_type="page_close"
                ),
                BaseModel: selector(event_source="server", event_type="base"),
                Server: selector(  # pylint: disable=unhashable-member
                    event_source="browser", event_type="page_close"
                ),
            },
            {
                Rule(LazyModelField("event_source"), "browser"): {
                    True: {
                        Rule(LazyModelField("event_type"), "page_close"): {
                            True: [UIPageClose, Server],
                            False: None,
                        }
                    },
                    False: {
                        Rule(LazyModelField("event_source"), "server"): {
                            True: {
                                Rule(LazyModelField("event_type"), "base"): {
                                    True: [BaseModel],
                                    False: None,
                                }
                            },
                            False: None,
                        }
                    },
                }
            },
        ),
        # Four models, multiple rules, with rules being subsets of other rules.
        (
            {
                UIPageClose: selector(  # pylint: disable=unhashable-member
                    event_source="browser"
                ),
                Server: selector(  # pylint: disable=unhashable-member
                    event_source="browser", event_type="page_close", page=None
                ),
                BaseModel: selector(event_source="server", event_type="base"),
                UISeqGoto: selector(  # pylint: disable=unhashable-member
                    event_source="browser", event_type="page_close"
                ),
            },
            {
                Rule(LazyModelField("event_source"), "browser"): {
                    True: {
                        Rule(LazyModelField("event_type"), "page_close"): {
                            True: {
                                Rule(LazyModelField("page"), None): {
                                    True: [Server],
                                    False: [UISeqGoto],
                                }
                            },
                            False: [UIPageClose],
                        },
                    },
                    False: {
                        Rule(LazyModelField("event_source"), "server"): {
                            True: {
                                Rule(LazyModelField("event_type"), "base"): {
                                    True: [BaseModel],
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
    """Given `model_rules` the ModelSelector should create the expected decision
    tree.
    """
    model_selector = ModelSelector(module="ralph.models.edx")
    assert model_selector.get_decision_tree(model_rules) == decision_tree


def test_models_selector_model_selector_get_model_with_invalid_event():
    """Test given an invalid event the get_model method should raise
    UnknownEventException.
    """
    with pytest.raises(UnknownEventException):
        ModelSelector(module="ralph.models.edx").get_first_model({"invalid": "event"})


@pytest.mark.parametrize(
    "module,model_rules",
    [
        (type("empty_module", (), {}), {}),
        (type("no_classes", (), {"int_member": 1, "str_member": "foo"}), {}),
        (
            type("not_a_subclass_of_base_model", (), {"not_base_model": dict}),
            {},
        ),
        (
            type("missing_selector_attribute", (), {"no_selector": BaseModel}),
            {},
        ),
        (
            type("one_valid_base_model", (), {"page_close": UIPageClose}),
            {
                UIPageClose: (  # pylint: disable=unhashable-member
                    UIPageClose.__selector__
                )
            },
        ),
        (
            type(
                "two_valid_base_models_and_other_members_to_ignore",
                (),
                {
                    "int_member": 1,
                    "page_close": UIPageClose,
                    "no_selector": BaseModel,
                    "not_base_model": dict,
                    "server": Server,
                    "str_member": "foo",
                },
            ),
            {
                UIPageClose: (  # pylint: disable=unhashable-member
                    UIPageClose.__selector__
                ),
                Server: Server.__selector__,  # pylint: disable=unhashable-member
            },
        ),
    ],
)
def test_models_selector_model_selector_build_model_rules(module, model_rules):
    """Given an imported module the `build_model_rules` method should return the
    corresponding model_rules.
    """
    assert ModelSelector.build_model_rules(module) == model_rules
