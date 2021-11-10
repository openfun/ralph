"""Model selector definition"""

from collections import Counter
from dataclasses import dataclass
from importlib import import_module
from inspect import getmembers, isclass
from itertools import chain
from types import ModuleType
from typing import Any, Type, Union

from pydantic import BaseModel

from ralph.defaults import MODEL_PATH_SEPARATOR
from ralph.exceptions import ModelRulesException, UnknownEventException
from ralph.utils import get_dict_value_from_path


@dataclass(frozen=True)
class LazyModelField:
    """Represents a model field."""

    path: tuple[str]

    def __init__(self, path: str):
        object.__setattr__(self, "path", tuple(path.split(MODEL_PATH_SEPARATOR)))


@dataclass(frozen=True)
class Rule:
    """Represents a rule used for selection."""

    field: LazyModelField
    value: Union[LazyModelField, Any]  # pylint: disable=unsubscriptable-object

    def check(self, event):
        """Checks if event matches the rule.

        Args:
            event (dict): The event to check.
        """

        event_value = get_dict_value_from_path(event, self.field.path)
        expected_value = self.value
        if isinstance(expected_value, LazyModelField):
            expected_value = get_dict_value_from_path(event, expected_value.path)
        return event_value == expected_value


class ModelRules(dict):
    """Stores the list of rules for each model."""

    def __setitem__(self, new_model: Type[BaseModel], new_rules: list[Rule]):
        """Inserts a new model with it's associated list of rules.

        Raises:
            ModelRulesException: When new_rules list is a subset or superset of
            another rules list.
        """

        rules_set = set(new_rules)
        for model, rules in self.items():
            if rules_set.issubset(rules) or rules_set.issuperset(rules):
                raise ModelRulesException(
                    f"{new_model.__name__} rules are a subset or superset "
                    f"of {model.__name__} rules"
                )
        super().__setitem__(new_model, new_rules)


def selector(**filters):
    """Returns a list of rules that should match in order to select an event.

    Args:
        **filters: Each keyword represents the path to a field, the corresponding
            value represents the value which the field should match.
            Example: `event_type="server"` will generate a Rule verifying that
            `event.event_type == "server"`
    """

    return [Rule(LazyModelField(field), value) for field, value in filters.items()]


class ModelSelector:
    """Selects the matching model for a given event.

    Attributes:
        model_rules (dict): Stores the list of rules for each model.
        decision_tree (dict): Stores the rule checking order for model selection.
    """

    def __init__(self, module="ralph.models.edx"):
        """Instantiates ModelSelector."""

        self.model_rules = ModelSelector.build_model_rules(import_module(module))
        self.decision_tree = self.get_decision_tree(self.model_rules)

    @staticmethod
    def build_model_rules(module: ModuleType):
        """Builds the model_rules dictionary from BaseModel classes defined
        in the module.
        """

        model_rules = ModelRules()
        for _, class_ in getmembers(module, isclass):
            if issubclass(class_, BaseModel) and hasattr(class_, "__selector__"):
                model_rules[class_] = class_.__selector__
        return model_rules

    def get_model(self, event: dict, tree=None):
        """Recursively walks through the decision tree to return the matching model
        for the event.

        Args:
            event (dict): Event to retrieve the corresponding model.
            tree (dict): The (sub) decision tree, `None` stands for the whole decision
                         tree.

        Returns:
            model (BaseModel): When the event matches all rules of the model.

        Raises:
            UnknownEventException: When the event does not match any model.
        """

        if tree is None:
            tree = self.decision_tree
        rule = next(iter(tree))
        is_valid = rule.check(event)
        subtree = tree[rule][is_valid]
        if not isinstance(subtree, dict):
            if subtree is None:
                raise UnknownEventException(
                    "No matching pydantic model found for input event"
                )
            # Here we have found the model.
            return subtree
        return self.get_model(event, subtree)

    def get_decision_tree(self, model_rules):
        """Recursively constructs the decision tree."""

        rule_counter = Counter(chain.from_iterable(model_rules.values()))
        if not rule_counter:
            return {}

        # We retrieve the rule with the highest occurrence and use it to split
        # the decision tree in two subtrees:
        # 1 - true_subtree: a subtree of models that require the most occurred
        #     rule to be true.
        # 2 - false_subtree: a subtree of models that don't use the most
        #     occurred rule.
        root_rule = rule_counter.most_common(1)[0][0]
        true_subtree = {}
        false_subtree = {}
        for model, rules in model_rules.items():
            if root_rule not in rules:
                false_subtree[model] = rules
                continue
            true_subtree[model] = list(filter(lambda rule: rule != root_rule, rules))

        if next(iter(true_subtree.values())):
            true_subtree = self.get_decision_tree(true_subtree)
        else:
            true_subtree = next(iter(true_subtree))
        false_subtree = self.get_decision_tree(false_subtree) if false_subtree else None

        return {root_rule: {True: true_subtree, False: false_subtree}}
