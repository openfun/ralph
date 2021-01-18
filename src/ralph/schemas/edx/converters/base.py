"""Converter Base Class"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from marshmallow import Schema, ValidationError

# xAPI module logger
logger = logging.getLogger(__name__)


def nested_get(dictionary, keys):
    """Get the nested dict value by keys array"""
    if keys is None:
        return None
    for key in keys:
        try:
            dictionary = dictionary[key]
        except (KeyError, TypeError):
            return None
    return dictionary


def nested_set(dictionary, keys, value):
    """Set the nested dict value by keys array"""
    for key in keys[:-1]:
        dictionary = dictionary.setdefault(key, {})
    dictionary[keys[-1]] = value


def nested_del(dictionary, keys):
    """Remove the nested dict key by keys array"""
    for key in keys[:-1]:
        if key not in dictionary:
            return
        dictionary = dictionary[key]
    if keys[-1] not in dictionary:
        return
    del dictionary[keys[-1]]


@dataclass
class GetFromField:
    """Stores the source path of a field and the transformer function"""

    path: str
    transformer: Callable = lambda x: x

    def __post_init__(self):
        self.path = self.path.split(">")

    def value(self, event):
        """Call transformer function and return the transformed value"""
        field = nested_get(event, self.path)
        return self.transformer(field)


class BaseConverter(ABC):
    """Converter Base Class

    Converters define a conversion dictionary to convert from one schema to another
    """

    _schema = Schema()

    def __init__(self):
        """Initialize BaseConverter"""

        self.conversion_dictionary = self.get_conversion_dictionary()
        self.field_array = []
        self.fill_field_array(self.conversion_dictionary, [])

    @abstractmethod
    def get_conversion_dictionary(self):
        """Returns a conversion dictionary used for conversion."""

    def fill_field_array(self, conversion_dictionary, path):
        """Fill field_array with all GetFromField's"""

        for key, value in conversion_dictionary.items():
            if isinstance(value, dict):
                path.append(key)
                self.fill_field_array(conversion_dictionary[key], path)
                path.pop()
            elif isinstance(value, GetFromField):
                self.field_array.append((path + [key], value))

    def convert(self, event):
        """Validates, Converts and Serializes event

        Args:
            event (dict): event to validate, convert and serialize

        Returns:
            (string): JSON serialized and converted event

        """
        try:
            self._schema.load(event)
        except ValidationError as err:
            logger.error("%s: Invalid event!", self.__class__.__name__)
            logger.debug("Error: %s \nFor Event %s", err, event)
            return None

        for key, value in self.field_array:
            field_value = value.value(event)
            if field_value in [None, "", {}]:
                nested_del(self.conversion_dictionary, key)
                continue
            nested_set(self.conversion_dictionary, key, field_value)

        return json.dumps(self.conversion_dictionary)
