"""Tests for the xAPI JSON-LD Profile."""
import json

import pytest
from pydantic import ValidationError

from ralph.models.selector import ModelSelector
from ralph.models.xapi.profile import Profile, ProfilePattern, ProfileTemplateRule

from tests.fixtures.hypothesis_strategies import custom_given


@custom_given(Profile)
def test_models_xapi_profile_with_json_ld_keywords(profile):
    """Test a `Profile` MAY include JSON-LD keywords."""
    profile = json.loads(profile.json(by_alias=True))
    profile["@base"] = None
    try:
        Profile(**profile)
    except ValidationError as err:
        pytest.fail(
            f"A profile including JSON-LD keywords should not raise exceptions: {err}"
        )


@pytest.mark.parametrize(
    "missing", [("prefLabel",), ("definition",), ("prefLabel", "definition")]
)
@custom_given(ProfilePattern)
def test_models_xapi_profile_pattern_with_invalid_primary_value(missing, pattern):
    """Test a `ProfilePattern` MUST include `prefLabel` and `definition` fields."""
    pattern = json.loads(pattern.json(by_alias=True))
    pattern["primary"] = True
    for field in missing:
        del pattern[field]

    msg = "A `primary` pattern MUST include `prefLabel` and `definition` fields"
    with pytest.raises(ValidationError, match=msg):
        ProfilePattern(**pattern)


@pytest.mark.parametrize(
    "rules",
    [
        (),
        ("alternates", "optional"),
        ("oneOrMore", "sequence"),
        ("zeroOrMore", "alternates"),
    ],
)
@custom_given(ProfilePattern)
def test_models_xapi_profile_pattern_with_invalid_number_of_match_rules(rules, pattern):
    """Test a `ProfilePattern` MUST contain exactly one of `alternates`, `optional`,
    `oneOrMore`, `sequence`, and `zeroOrMore`.
    """
    rule_values = {
        "alternates": ["https://example.com", "https://example.fr"],
        "optional": "https://example.com",
        "oneOrMore": "https://example.com",
        "sequence": ["https://example.com", "https://example.fr"],
        "zeroOrMore": "https://example.com",
    }
    pattern = json.loads(pattern.json(by_alias=True))
    del pattern["optional"]
    for rule in rules:
        pattern[rule] = rule_values[rule]

    msg = (
        "A pattern MUST contain exactly one of `alternates`, `optional`, "
        "`oneOrMore`, `sequence`, and `zeroOrMore` fields"
    )
    with pytest.raises(ValidationError, match=msg):
        ProfilePattern(**pattern)


@custom_given(Profile)
def test_models_xapi_profile_selector_with_valid_model(profile):
    """Test given a valid profile, the `get_first_model` method of the model
    selector should return the corresponding model.
    """
    profile = json.loads(profile.json())
    model_selector = ModelSelector(module="ralph.models.xapi.profile")
    assert model_selector.get_first_model(profile) is Profile


@pytest.mark.parametrize("field", ["location", "selector"])
@custom_given(ProfileTemplateRule)
def test_models_xapi_profile_template_rules_with_invalid_json_path(field, rule):
    """Test given a profile template rule with a `location` or `selector` containing an
    invalid JSONPath, the `ProfileTemplateRule` model should raise an exception.
    """
    rule = json.loads(rule.json())
    rule[field] = ""
    msg = "Invalid JSONPath: empty string is not a valid path"
    with pytest.raises(ValidationError, match=msg):
        ProfileTemplateRule(**rule)

    rule[field] = "not a JSONPath"
    msg = (
        f"1 validation error for ProfileTemplateRule\n{field}\n  Invalid JSONPath: "
        r"Parse error at 1:4 near token a \(ID\) \(type=value_error\)"
    )
    with pytest.raises(ValidationError, match=msg):
        ProfileTemplateRule(**rule)


@pytest.mark.parametrize("field", ["location", "selector"])
@custom_given(ProfileTemplateRule)
def test_models_xapi_profile_template_rules_with_valid_json_path(field, rule):
    """Test given a profile template rule with a `location` or `selector` containing an
    valid JSONPath, the `ProfileTemplateRule` model should not raise exceptions.
    """
    rule = json.loads(rule.json())
    rule[field] = "$.context.extensions['http://example.com/extension']"
    try:
        ProfileTemplateRule(**rule)
    except ValidationError as err:
        pytest.fail(
            "A `ProfileTemplateRule` with a valid JSONPath should not raise exceptions:"
            f" {err}"
        )


@custom_given(Profile)
def test_models_xapi_profile_with_valid_json_schema(profile):
    """Test given a profile with an extension concept containing a valid JSONSchema,
    should not raise exceptions.
    """
    profile = json.loads(profile.json(by_alias=True))
    profile["concepts"] = [
        {
            "id": "http://example.com",
            "type": "ContextExtension",
            "inScheme": "http://example.profile.com",
            "prefLabel": {
                "en-us": "Example context extension",
            },
            "definition": {
                "en-us": "To use when an example happens",
            },
            "inlineSchema": json.dumps(
                {
                    "$id": "https://example.com/example.schema.json",
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "Example",
                    "type": "object",
                    "properties": {
                        "example": {"type": "string", "description": "The example."},
                    },
                }
            ),
        }
    ]
    try:
        Profile(**profile)
    except ValidationError as err:
        pytest.fail(
            f"A profile including a valid JSONSchema should not raise exceptions: {err}"
        )


@custom_given(Profile)
def test_models_xapi_profile_with_invalid_json_schema(profile):
    """Test given a profile with an extension concept containing an invalid JSONSchema,
    should raise an exception.
    """
    profile = json.loads(profile.json(by_alias=True))
    profile["concepts"] = [
        {
            "id": "http://example.com",
            "type": "ContextExtension",
            "inScheme": "http://example.profile.com",
            "prefLabel": {
                "en-us": "Example context extension",
            },
            "definition": {
                "en-us": "To use when an example happens",
            },
            "inlineSchema": json.dumps({"type": "example"}),
        }
    ]
    msg = "Invalid JSONSchema: 'example' is not valid under any of the given schemas"
    with pytest.raises(ValidationError, match=msg):
        Profile(**profile)
