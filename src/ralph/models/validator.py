"""Event validator definition."""


import json
import logging
from typing import TextIO

from pydantic import ValidationError

from ralph.exceptions import BadFormatException, UnknownEventException
from ralph.models.selector import ModelSelector

logger = logging.getLogger(__name__)


class Validator:
    """Events validator using pydantic models."""

    def __init__(self, model_selector: ModelSelector):
        """Initializes Validator."""
        self.model_selector = model_selector

    def validate(self, input_file: TextIO, ignore_errors: bool, fail_on_unknown: bool):
        """Validates JSON event strings line by line."""
        total = 0
        success = 0
        for event_str in input_file:
            try:
                total += 1
                yield self._validate_event(event_str)
                success += 1
            except (json.JSONDecodeError, TypeError) as err:
                message = "Input event is not a valid JSON string"
                self._log_error(message, event_str, err)
                if not ignore_errors:
                    raise BadFormatException(message) from err
            except UnknownEventException as err:
                self._log_error(err, event_str)
                if fail_on_unknown:
                    raise err
            except ValidationError as err:
                message = f"Input event is not a valid {err.model.__name__} event."
                self._log_error(message, event_str, err)
                if not ignore_errors:
                    raise BadFormatException(message) from err
        logger.info("Total events: %d, Invalid events: %d", total, total - success)

    def get_first_valid_model(self, event: dict):
        """Returns the first successfully instantiated model for the event.

        Raises:
            UnknownEventException: When the event does not match any model.
            ValidationError: When the last validated event is invalid.
        """
        error = None
        for model in self.model_selector.get_models(event):
            try:
                return model(**event)
            except ValidationError as err:
                error = err

        raise error

    def _validate_event(self, event_str: str):
        """Validate a single JSON string event.

        Raises:
            TypeError: When the event_str is not of type string.
            JSONDecodeError: When the event_str is not a valid JSON string.
            UnknownEventException: When no matching model is found for the event.
            ValidationError: When the event is failing the pydantic model validation.

        Returns:
            event_str (str): The cleaned JSON-formatted input event_str.
        """
        event = json.loads(event_str)
        return self.get_first_valid_model(event).json()

    @staticmethod
    def _log_error(message, event_str, error=None):
        logger.error(message)
        logger.debug("Raised error: %s, for event : %s", error, event_str)
