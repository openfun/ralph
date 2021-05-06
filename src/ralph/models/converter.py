"""Base converter definition"""

from abc import ABC, abstractmethod
from uuid import UUID, uuid5

from pydantic import BaseModel

from ralph.defaults import EDX_UUID_NAMESPACE, MODEL_PATH_SEPARATOR
from ralph.exceptions import ConversionException
from ralph.utils import (
    get_dict_value_from_path,
    remove_dict_key_from_path,
    set_dict_value_from_path,
)


class BaseConverter(ABC):
    """Converter Base Class.

    Converters define a conversion set to convert from one event type to another.
    """

    __model__: BaseModel

    def __init__(self):
        """Initializes BaseConverter."""

        self.conversion_dict = {}
        self.field_array = []
        for field in self.get_conversion_set():
            destination_path = field[0].split(MODEL_PATH_SEPARATOR)
            value = field[1]() if callable(field[1]) else None
            set_dict_value_from_path(self.conversion_dict, destination_path, value)
            if not value:
                transformer = field[2] if len(field) == 3 else lambda x: x
                source_path = field[1].split(MODEL_PATH_SEPARATOR)
                self.field_array.append((destination_path, source_path, transformer))

    @abstractmethod
    def get_conversion_set(self):
        """Returns a conversion set used for conversion."""

    def convert(self, event: dict, event_str: str):
        """Converts and serializes the event.

        Args:
            event (dict): the event to convert and serialize.
            event_str (str): the event original string value.
        Returns:
            (string): converted and JSON serialized event.
        """

        for destination_path, source_path, transformer in self.field_array:
            field = get_dict_value_from_path(event, source_path)
            transformed_field = transformer(field)
            if transformed_field in [None, "", {}]:
                remove_dict_key_from_path(self.conversion_dict, destination_path)
                continue
            set_dict_value_from_path(
                self.conversion_dict, destination_path, transformed_field
            )

        self.conversion_dict["id"] = self.get_event_uuid5(event_str)
        return self.__model__(**self.conversion_dict).json(
            exclude_none=True, by_alias=True
        )

    @staticmethod
    def get_event_uuid5(event: str):
        """Returns a constant UUID5 based on the given event string."""

        try:
            return uuid5(UUID(EDX_UUID_NAMESPACE), event)
        except (TypeError, ValueError) as err:
            raise ConversionException(
                "Invalid EDX_UUID_NAMESPACE configuration.", err
            ) from err
