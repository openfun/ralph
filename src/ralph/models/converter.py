"""Converter methods definition"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from inspect import getmembers, isclass
from types import ModuleType
from typing import Any, Callable, TextIO, Union

from pydantic import BaseModel, ValidationError

from ralph.defaults import MODEL_PATH_SEPARATOR
from ralph.exceptions import (
    BadFormatException,
    ConversionException,
    MissingConversionSetException,
    UnknownEventException,
)
from ralph.utils import get_dict_value_from_path, set_dict_value_from_path

from .selector import ModelSelector

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversionItem:
    """Represents a conversion set item."""

    dest: tuple[str]
    src: Union[tuple[str], str, None]
    transformers: tuple[Callable[[Any], Any]]
    raw_input: bool

    def __init__(self, dest: str, src=None, transformers=lambda _: _, raw_input=False):
        """Initializes ConversionItem.

        Args:
            dest (str): The destination path where to place the converted value.
            src (str or None): The source from where the value to convert is fetched.
                - When `src` is a path (ex. `context__user_id`) - the value is the item
                    of the event at the path.
                - When `src` is `None` - the value is the whole event.
            transformers (function or tuple of functions): The function(s) to apply on the source
                value.
            raw_input (bool): Flag indicating whether `get_value` will receive a raw event string
                or a parsed event dictionary.
        """

        object.__setattr__(self, "dest", tuple(dest.split(MODEL_PATH_SEPARATOR)))
        src = tuple(src.split(MODEL_PATH_SEPARATOR)) if src else None
        object.__setattr__(self, "src", src)
        transformers = tuple([transformers]) if callable(transformers) else transformers
        object.__setattr__(self, "transformers", transformers)
        object.__setattr__(self, "raw_input", raw_input)

    def get_value(self, data: Union[dict, str]):
        """Returns fetched source value after having applied all transformers to it.

        Args:
            data (dict or string): The event to convert.

        Raises:
            ConversionException: When a field transformation fails.
        """

        if self.src:
            data = get_dict_value_from_path(data, self.src)
        try:
            for transformer in self.transformers:
                data = transformer(data)
        except Exception as err:
            msg = f"Failed to get the transformed value for field: {self.src}"
            raise ConversionException(msg) from err
        return data


class BaseConversionSet(ABC):
    """ConversionSet Base Class.

    ConversionSets are used to convert from one event format to another.
    """

    __src__: BaseModel
    __dest__: BaseModel

    def __init__(self):
        """Initializes BaseConversionSet."""

        self._conversion_items = self._get_conversion_items()

    @abstractmethod
    def _get_conversion_items(self) -> set[ConversionItem]:
        """Returns a set of ConversionItems used for conversion."""

    def __iter__(self):
        return iter(self._conversion_items)


def convert_dict_event(
    event: dict, event_str: str, conversion_set: BaseConversionSet
) -> BaseModel:
    """Converts the event dictionary using the provided original event string and conversion_set.

    Args:
        event (dict): The event to convert.
        event_str (dict): The original event string.
        conversion_set (BaseConversionSet): A conversion set used for conversion.

    Returns:
        event (BaseModel): The converted event pydantic model.

    Raises:
        ConversionException: When a field transformation fails.
        ValidationError: When the final converted event is invalid.
    """

    converted_event = {}
    for conversion_item in conversion_set:
        data = event_str if conversion_item.raw_input else event
        value = conversion_item.get_value(data)
        if value not in [None, "", {}]:
            set_dict_value_from_path(converted_event, conversion_item.dest, value)
    logger.debug("Intermediate converted event: %s", converted_event)
    return conversion_set.__dest__(**converted_event)


def convert_str_event(event_str: str, conversion_set: BaseConversionSet) -> BaseModel:
    """Converts the event string using the provided conversion_set.

    Args:
        event_str (str): The event to convert.
        conversion_set (BaseConversionSet): A conversion set used for conversion.

    Returns:
        event (BaseModel): The converted event pydantic model.

    Raises:
        BadFormatException: When the event_str is not a valid JSON string.
        ConversionException: When a field transformation fails.
        ValidationError: When the converted event is invalid.
    """

    try:
        event = json.loads(event_str)
    except (TypeError, json.JSONDecodeError) as err:
        msg = "Failed to parse the event, invalid JSON string"
        raise BadFormatException(msg) from err
    return convert_dict_event(event, event_str, conversion_set)


class Converter:
    """Converts events using pydantic models."""

    def __init__(
        self,
        model_selector=ModelSelector(),
        module="ralph.models.edx.converters.xapi",
        **conversion_set_kwargs,
    ):
        """Initializes the Converter."""

        self.model_selector = model_selector
        self.src_conversion_set = self.get_src_conversion_set(
            import_module(module), **conversion_set_kwargs
        )

    @staticmethod
    def get_src_conversion_set(module: ModuleType, **conversion_set_kwargs):
        """Returns a dictionary of initialized conversion_sets defined in the module."""

        src_conversion_set = {}
        for _, class_ in getmembers(module, isclass):
            if issubclass(class_, BaseConversionSet):
                src_conversion_set[class_.__src__] = class_(**conversion_set_kwargs)
        return src_conversion_set

    def convert(self, input_file: TextIO, ignore_errors: bool, fail_on_unknown: bool):
        """Converts JSON event strings line by line."""

        total = 0
        success = 0
        for event_str in input_file:
            try:
                total += 1
                yield self._convert_event(event_str).json(
                    exclude_none=True, by_alias=True
                )
                success += 1
            except (TypeError, json.JSONDecodeError) as err:
                message = "Input event is not a valid JSON string"
                self._log_error(message, event_str, err)
                if not ignore_errors:
                    raise BadFormatException(message) from err
            except (UnknownEventException, MissingConversionSetException) as err:
                self._log_error(err, event_str)
                if fail_on_unknown:
                    raise err
            except ConversionException as err:
                self._log_error(err, event_str)
                if not ignore_errors:
                    raise err
            except ValidationError as err:
                message = f"Converted event is not a valid ({err.model}) model"
                self._log_error(message, event_str, err)
                if not ignore_errors:
                    raise err
        logger.info("Total events: %d, Invalid events: %d", total, total - success)

    def _convert_event(self, event_str: str):
        """Converts a single JSON string event.

        Args:
            event_str (str): The event to convert.

        Returns:
            event (BaseModel): The converted event pydantic model.

        Raises:
            TypeError: When the event_str is not of type string.
            JSONDecodeError: When the event_str is not a valid JSON string.
            UnknownEventException: When no matching model is found for the event.
            MissingConversionSetException: When no matching conversion set is found for the event.
            ConversionException: When a field transformation fails.
            ValidationError: When the final converted event is invalid.
        """

        event = json.loads(event_str)
        model = self.model_selector.get_model(event)
        conversion_set = self.src_conversion_set.get(model, None)
        if not conversion_set:
            message = "No conversion set found for input event"
            raise MissingConversionSetException(message)
        return convert_dict_event(event, event_str, conversion_set)

    @staticmethod
    def _log_error(message, event_str, error=None):
        logger.error(message)
        logger.debug("Raised error: %s, for event : %s", error, event_str)
