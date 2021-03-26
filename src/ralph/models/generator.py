"""generate_json_schemas definition"""

import json
import logging
import re
from typing import TextIO

from genson import SchemaBuilder

from ralph.exceptions import UnknownEventException
from ralph.models.selector import ModelSelector

logger = logging.getLogger(__name__)


def replace_pattern_properties(event):
    """Replaces pattern properties matching regex with a single pattern.

    This reduces the JSON schema size, genson treats each pattern property as an optional property.

    Example:
        Replaces `cc2a00e69f7a4dd8b560f4e48911206f_3_1` with `MD5HASH_int_int_0`.
    """

    count = 0
    result = {}
    for key, item in event.items():
        if re.match(r"^[a-f0-9]{32}_[0-9]+_[0-9]+$", key):
            key = f"MD5HASH_int_int_{count}"
            count += 1
        if isinstance(item, dict):
            result[key] = replace_pattern_properties(item)
            continue
        result[key] = item
    return result


def generate_json_schemas(input_file: TextIO, model_selector: ModelSelector):
    """Generates JSON schemas reading from input file line by line."""

    json_schemas = {}
    for event_str in input_file:
        try:
            # Parse the event and check if it's Unknown.
            event = json.loads(event_str)
            model_selector.get_model(event)
        except (json.JSONDecodeError, TypeError):
            message = "Input event is not a valid JSON string"
            logger.error(message)
        except UnknownEventException:
            # Event is unknown.
            if "event_source" not in event or "event_type" not in event:
                continue
            event = replace_pattern_properties(event)
            # The title of browser event `seq_goto` should be `SeqGotoBrowserEventModel`.
            title = f"{event['event_type']}.{event['event_source']}.event.model"
            title = "".join(x.capitalize() for x in title.replace("_", ".").split("."))
            builder = SchemaBuilder()
            # Retrieve the schema by title, if we have already defined it before or use a new one.
            new_schema = {"title": title, "type": "object", "properties": {}}
            builder.add_schema(json_schemas.get(title, new_schema))
            # Update the schema with the current event.
            builder.add_object(event)
            # Store the updated schema in json_schemas.
            json_schemas[title] = builder.to_schema()

    for schema in json_schemas.values():
        yield json.dumps(schema)
