"""Generate markdown documentation"""

import ast
import inspect
import json
import os
import re
import types

from marshmallow.fields import Nested
from marshmallow.validate import URL, Equal

from ralph.schemas.edx.converters.base import GetFromField
from ralph.schemas.edx.converters.xapi_converter_selector import Converters

from tests.schemas.edx.converters.xapi.test_tincan import CONVERTER_EVENTS

OPENFUN_GITHUB = "https://github.com/openfun/edx-platform"
OPENFUN_VERSION = f"{OPENFUN_GITHUB}/blob/0e0baa298ad4067accaa5129bffd2457636d4e3f"


def get_validation_rules(field_type):
    """Returns a string of validation rules explanations"""

    validation_rules = []
    for validator in field_type.validators:
        if isinstance(validator, Equal):
            validation_rules.append(f"Equal to `{str(validator.comparable)}`")
        if isinstance(validator, URL):
            validation_rules.append(
                ("Allow" if validator.relative else "Disallow") + " relative URL"
            )
    return "\n".join(validation_rules)


def get_fields(fields, field_doc_string, field_validator_doc_string, schema_path):
    """Returns a dictionary of fields with information about (type/required/nullable...)"""

    output = {}
    for field_name, field_type in fields.items():
        field_type_name = field_type.__class__.__name__
        field_info = {
            "type": "Any" if field_type_name == "Field" else field_type_name,
            "required": "YES" if field_type.required else "NO",
            "nullable": "YES" if field_type.allow_none else "NO",
            "validation_rules": get_validation_rules(field_type),
            "validator_doc_string": field_validator_doc_string.get(field_name, ""),
            "doc_string": field_doc_string.get(field_name, "No docs")
        }
        if isinstance(field_type, Nested):
            field_info["schema"] = f"./{field_type.schema.__class__.__name__}.md"
            write_schema(field_type.schema, schema_path)
        output[field_name] = field_info
    return output


def get_field_doc_string(class_type):
    """Returns a dictionary containing the class fields with their corresponding doc string."""

    field_doc_string = {}
    for base_type in class_type.__mro__[:-3]:
        with open(inspect.getfile(base_type), "r") as file:
            source = file.read()
        for node in ast.parse(source).body:
            if isinstance(node, ast.ClassDef) and node.name == base_type.__name__:
                previous_attribute = None
                for class_node in node.body:
                    if isinstance(class_node, ast.Assign):
                        previous_attribute = class_node.targets[0].id
                    if isinstance(class_node, ast.Expr) and previous_attribute is not None:
                        field_doc_string[previous_attribute] = class_node.value.value
                        previous_attribute = None
    return field_doc_string


def get_field_validator_doc_string(schema_class):
    """Returns a dictionary containing fields with their corresponding validator doc string"""

    # pylint:disable=protected-access
    field_validators = schema_class._hooks["validates"]
    return {x.partition('_')[2]: getattr(schema_class, x).__doc__ for x in field_validators}


def get_schema_validator_doc_string(schema_class):
    """Returns a dictionary with schema validation function names and doc string keys"""

    # pylint:disable=protected-access
    schema_validators = schema_class._hooks[("validates_schema", False)]
    return {x: remove_intend(getattr(schema_class, x).__doc__, 2) for x in schema_validators}


def remove_intend(text, depth=1):
    "Returns text with removed indentation and trailing white spaces"

    return "\n".join(re.sub(f"^{'    ' * depth}", "", line) for line in text.split("\n")).rstrip()


def format_field_doc_string(doc_string):
    """Returns a formatted field doc string"""

    # print(doc_string.split("Source:\n"))
    re_match = re.match(
        r"^(?P<description>.*)Source:\n        (?P<source>.*)\n",
        doc_string,
        re.DOTALL
    )
    source = OPENFUN_VERSION + re_match.group("source")
    doc_string = re_match.group("description") + f"<a href='{source}'>Source</a>"
    return doc_string.replace("\n", "<br>")


def get_field_table(schema, schema_path):
    """Writes the field documentation for a given schema"""

    field_doc_string = get_field_doc_string(schema.__class__)
    field_validator_doc_string = get_field_validator_doc_string(schema)
    fields = get_fields(schema.fields, field_doc_string, field_validator_doc_string, schema_path)
    content = "Name|Type|Required|Nullable|Validation|Documentation\n"
    content += "----|----|--------|--------|----------|-------------\n"
    for key in sorted(fields):
        field = fields[key]
        name = "<a href='{}'>{}</a>".format(field["schema"], key) if "schema" in field else key
        content += name + f"<div id='{key.lower()}'></div>|"
        content += field["type"] + "|"
        content += field["required"] + "|"
        content += field["nullable"] + "|"
        content += field["validation_rules"] + "<br>"
        content += field["validator_doc_string"].replace("\n", "<br>") + "|"
        content += format_field_doc_string(field["doc_string"]) + "\n"
    return content


def get_field_link(schema, path):
    """Returns a link to the field for the schema"""

    links = []
    for field_name in path:
        fields = schema.fields
        schema_name = schema.__class__.__name__
        links.append(
            f"[{field_name}]"
            f"(./../schemas/{schema_name}.md"
            f"#user-content-{field_name.lower()})"
        )
        if isinstance(fields[field_name], Nested):
            schema = fields[field_name].schema
    return ">".join(links)


def get_flat_conversion_dict(schema, conversion_dict, depth=""):
    """Returns a flattened conversion dictionary"""

    flat_conversion_dict = {}
    transformers = []
    for key, value in sorted(conversion_dict.items()):
        key = key if depth == "" else f"{depth}>{key}"
        if isinstance(value, dict):
            nested_conversion_dict, nested_transfromers = get_flat_conversion_dict(
                schema, value, key
            )
            flat_conversion_dict.update(nested_conversion_dict)
            transformers.extend(nested_transfromers)
            continue
        if not isinstance(value, GetFromField):
            flat_conversion_dict[key] = value
            continue
        field = get_field_link(schema, value.path)
        if isinstance(value.transformer, types.LambdaType):
            transformer = inspect.getsource(value.transformer).strip()
            if transformer == "transformer: Callable = lambda x: x":
                flat_conversion_dict[key] = f"GetFromField({field})"
                continue
            transformer = re.match(r"^.*(lambda.*)", transformer, re.DOTALL).groups()[0]
            flat_conversion_dict[key] = f"GetFromField({field}, {transformer})"
            continue
        name = value.transformer.__name__
        flat_conversion_dict[key] = f"GetFromField({field}, [{name}](#{name}))"
        transformers.append(value.transformer)
    return flat_conversion_dict, transformers


def get_conversion_table(conversion_dict):
    """Writes markdown documentation table for conversion dict"""

    content = "Name|Value\n"
    content += "----|----\n"
    for name in sorted(conversion_dict):
        content += f"{name}|{conversion_dict[name]}\n"
    return content


class MarkdownDocument:
    """Represents a Markdown document"""

    def __init__(self):
        self.content = '\n'.join((
            "<!-- ",
            "    This document has been automatically generated.",
            "    It should NOT BE EDITED.",
            "    To update this part of the documentation,",
            "    please type the following from the repository root:",
            "    $ make docs",
            "-->",
            "",
        ))

    def add_line(self, line):
        """Adds the line to the markdown content"""

        self.content += f"{line}\n\n"

    def add_header(self, header, level=1):
        """Adds a header to the markdown document"""

        self.add_line(f"{'#' * level} {header}")

    def add_json(self, json_string):
        """Add the JSON string to the markdown content"""

        self.add_line(f"```json\n{json_string}\n```")

    def save(self, name):
        """Save MarkdownWriter.content to file"""

        file_name = f"{name}.md"
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w") as file:
            file.write(self.content)


def write_schema(schema, schema_path, example=None):
    """Writes the documentation for a given schema to a file"""

    doc = MarkdownDocument()
    doc.add_header(schema.__class__.__name__)
    doc.add_line(remove_intend(schema.__doc__))
    if example:
        doc.add_header("Example", 2)
        doc.add_json(json.dumps(example, indent=4, sort_keys=True))
    doc.add_header("Fields", 2)
    doc.add_line(get_field_table(schema, schema_path))
    doc.add_header("Schema validation", 2)
    for schema_validator, doc_string in get_schema_validator_doc_string(schema).items():
        doc.add_header(schema_validator, 3)
        doc.add_line(doc_string)
    doc.save(schema_path + schema.__class__.__name__)


def write_converter(converter, path, example):
    """Writes the documentation for a given converter to a file"""

    # pylint:disable=protected-access
    write_schema(converter._schema, f"{path}/schemas/", example)
    converter_instance = converter("https://fun-mooc.fr")
    conversion_dict = converter_instance.get_conversion_dictionary()
    conversion_dict, transformers = get_flat_conversion_dict(converter._schema, conversion_dict)
    schema_name = converter._schema.__class__.__name__
    doc = MarkdownDocument()
    doc.add_header(converter.__name__)
    doc.add_line(remove_intend(converter.__doc__))
    doc.add_header(f"Schema: [{schema_name}](./../schemas/{schema_name}.md)", 2)
    doc.add_header("Example", 2)
    doc.add_json(
        json.dumps(json.loads(converter_instance.convert(example)), indent=4, sort_keys=True)
    )
    doc.add_header("Conversion table", 2)
    doc.add_line(get_conversion_table(conversion_dict))
    if transformers:
        doc.add_header("Transformers", 2)
    for transformer in transformers:
        doc.add_header(transformer.__name__, 3)
        doc.add_line(remove_intend(transformer.__doc__, 2))
    doc.save(f"{path}/converters/{converter.__name__}")


def main(path):
    """Entrypoint"""

    schema_example = {}
    for converter_event in CONVERTER_EVENTS:
        schema_example[converter_event[0]] = converter_event[1][1][0]
    for converter_enum in Converters:
        write_converter(converter_enum.value, path, schema_example[converter_enum])


if __name__ == "__main__":
    main('docs')
