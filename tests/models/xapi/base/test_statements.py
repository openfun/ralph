"""Tests for the BaseXapiStatement."""

import json

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from pydantic import ValidationError

from ralph.models.selector import ModelSelector
from ralph.models.xapi.base.agents import BaseXapiAgentWithAccount
from ralph.models.xapi.base.groups import (
    BaseXapiAnonymousGroup,
    BaseXapiIdentifiedGroupWithAccount,
    BaseXapiIdentifiedGroupWithMbox,
    BaseXapiIdentifiedGroupWithMboxSha1Sum,
    BaseXapiIdentifiedGroupWithOpenId,
)
from ralph.models.xapi.base.objects import BaseXapiSubStatement
from ralph.models.xapi.base.statements import BaseXapiStatement
from ralph.models.xapi.base.unnested_objects import (
    BaseXapiActivity,
    BaseXapiActivityInteractionDefinition,
    BaseXapiStatementRef,
)
from ralph.utils import set_dict_value_from_path

from tests.fixtures.hypothesis_strategies import custom_builds, custom_given


@pytest.mark.parametrize(
    "path",
    ["id", "stored", "verb__display", "context__contextActivities__parent"],
)
@pytest.mark.parametrize("value", [None, "", {}])
@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_with_invalid_null_values(path, value, statement):
    """Test that the statement does not accept any null values.

    XAPI-00001
    An LRS rejects with error code 400 Bad Request any Statement having a property whose
    value is set to "null", an empty object, or has no value, except in an "extensions"
    property.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="invalid empty value"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path",
    [
        "object__definition__extensions__https://w3id.org/xapi/video",
        "result__extensions__https://w3id.org/xapi/video",
        "context__extensions__https://w3id.org/xapi/video",
    ],
)
@pytest.mark.parametrize("value", [None, "", {}])
@custom_given(custom_builds(BaseXapiStatement, object=custom_builds(BaseXapiActivity)))
def test_models_xapi_base_statement_with_valid_null_values(path, value, statement):
    """Test that the statement does accept valid null values in extensions fields.

    XAPI-00001
    An LRS rejects with error code 400 Bad Request any Statement having a property whose
    value is set to "null", an empty object, or has no value, except in an "extensions"
    property.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    try:
        BaseXapiStatement(**statement)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")


@pytest.mark.parametrize("path", ["object__definition__correctResponsesPattern"])
@custom_given(
    custom_builds(
        BaseXapiStatement,
        object=custom_builds(
            BaseXapiActivity,
            definition=custom_builds(BaseXapiActivityInteractionDefinition),
        ),
    )
)
def test_models_xapi_base_statement_with_valid_empty_array(path, statement):
    """Test that the statement does accept a valid empty array.

    Where the Correct Responses Pattern contains an empty array, the meaning of this is
    that there is no correct answer.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), [])
    try:
        BaseXapiStatement(**statement)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "field",
    ["actor", "verb", "object"],
)
@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_must_use_actor_verb_and_object(field, statement):
    """Test that the statement raises an exception if required fields are missing.

    XAPI-00003
    An LRS rejects with error code 400 Bad Request a Statement which does not contain an
    "actor" property.
    XAPI-00004
    An LRS rejects with error code 400 Bad Request a Statement which does not contain a
    "verb" property.
    XAPI-00005
    An LRS rejects with error code 400 Bad Request a Statement which does not contain an
    "object" property.
    """
    statement = statement.dict(exclude_none=True)
    del statement[field]
    with pytest.raises(ValidationError, match="field required"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path,value",
    [
        ("actor__name", 1),  # Should be a string
        ("actor__account__name", 1),  # Should be a string
        ("actor__account__homePage", 1),  # Should be an IRI
        ("actor__account", ["foo", "bar"]),  # Should be a dictionary
        ("verb__display", ["foo"]),  # Should be a dictionary
        ("verb__display", {"en": 1}),  # Should have string values
        ("object__id", ["foo"]),  # Should be an IRI
    ],
)
@custom_given(
    custom_builds(BaseXapiStatement, actor=custom_builds(BaseXapiAgentWithAccount))
)
def test_models_xapi_base_statement_with_invalid_data_types(path, value, statement):
    """Test that the statement does not accept values with wrong types.

    XAPI-00006
    An LRS rejects with error code 400 Bad Request a Statement which uses the wrong data
    type.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    err = "(type expected|not a valid dict|expected string )"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path,value",
    [
        ("id", "0545fe73-1bbd-4f84-9c9a"),  # Should be a valid UUID
        ("actor", {"mbox": "example@mail.com"}),  # Should be a Mailto IRI
        ("verb__display", {"bad language tag": "foo"}),  # Should be a valid LanguageTag
        ("object__id", ["This is not an IRI"]),  # Should be an IRI
    ],
)
@custom_given(
    custom_builds(BaseXapiStatement, actor=custom_builds(BaseXapiAgentWithAccount))
)
def test_models_xapi_base_statement_with_invalid_data_format(path, value, statement):
    """Test that the statement does not accept values having a wrong format.

    XAPI-00007
    An LRS rejects with error code 400 Bad Request a Statement which uses any
    non-format-following key or value, including the empty string, where a string with a
    particular format (such as mailto IRI, UUID, or IRI) is required.
    (Empty strings are covered by XAPI-00001)
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    err = "(Invalid `mailto:email`|Invalid RFC 5646 Language tag|not a valid uuid)"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize("path,value", [("actor__objecttype", "Agent")])
@custom_given(
    custom_builds(BaseXapiStatement, actor=custom_builds(BaseXapiAgentWithAccount))
)
def test_models_xapi_base_statement_with_invalid_letter_cases(path, value, statement):
    """Test that the statement does not accept keys having invalid letter cases.

    XAPI-00008
    An LRS rejects with error code 400 Bad Request a Statement where the case of a key
    does not match the case specified in this specification.
    """
    statement = statement.dict(exclude_none=True)
    if statement["actor"].get("objectType", None):
        del statement["actor"]["objectType"]
    set_dict_value_from_path(statement, path.split("__"), value)
    err = "(unexpected value|extra fields not permitted)"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_should_not_accept_additional_properties(statement):
    """Test that the statement does not accept additional properties.

    XAPI-00010
    An LRS rejects with error code 400 Bad Request a Statement where a key or value is
    not allowed by this specification.
    """
    invalid_statement = statement.dict(exclude_none=True)
    invalid_statement["NEW_INVALID_FIELD"] = "some value"
    with pytest.raises(ValidationError, match="extra fields not permitted"):
        BaseXapiStatement(**invalid_statement)


@pytest.mark.parametrize("path,value", [("object__id", "w3id.org/xapi/video")])
@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_with_iri_without_scheme(path, value, statement):
    """Test that the statement does not accept IRIs without a scheme.

    XAPI-00011
    An LRS rejects with error code 400 Bad Request a Statement containing IRL or IRI
    values without a scheme.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="is not a valid 'IRI'"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path",
    [
        "object__definition__extensions__foo",
        "result__extensions__1",
        "context__extensions__w3id.org/xapi/video",
    ],
)
@custom_given(custom_builds(BaseXapiStatement, object=custom_builds(BaseXapiActivity)))
def test_models_xapi_base_statement_with_invalid_extensions(path, statement):
    """Test that the statement does not accept extensions keys with invalid IRIs.

    XAPI-00118
    An Extension "key" is an IRI. The LRS rejects with 400 a statement which has an
    extension key which is not a valid IRI, if an extension object is present.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), "")
    with pytest.raises(ValidationError, match="is not a valid 'IRI'"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize("path,value", [("actor__mbox", "mailto:example@mail.com")])
@custom_given(
    custom_builds(BaseXapiStatement, actor=custom_builds(BaseXapiAgentWithAccount))
)
def test_models_xapi_base_statement_with_two_agent_types(path, value, statement):
    """Test that the statement does not accept multiple agent types.

    An Agent MUST NOT include more than one Inverse Functional Identifier.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="extra fields not permitted"):
        BaseXapiStatement(**statement)


@custom_given(
    custom_builds(BaseXapiStatement, actor=custom_builds(BaseXapiAnonymousGroup))
)
def test_models_xapi_base_statement_missing_member_property(statement):
    """Test that the statement does not accept group agents with missing members.

    An Anonymous Group MUST include a "member" property listing constituent Agents.
    """
    statement = statement.dict(exclude_none=True)
    del statement["actor"]["member"]
    with pytest.raises(ValidationError, match="member\n  field required"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "value",
    [
        BaseXapiAnonymousGroup,
        BaseXapiIdentifiedGroupWithMbox,
        BaseXapiIdentifiedGroupWithMboxSha1Sum,
        BaseXapiIdentifiedGroupWithOpenId,
        BaseXapiIdentifiedGroupWithAccount,
    ],
)
@custom_given(
    st.one_of(
        custom_builds(BaseXapiStatement, actor=custom_builds(BaseXapiAnonymousGroup)),
        custom_builds(
            BaseXapiStatement,
            actor=custom_builds(BaseXapiIdentifiedGroupWithMbox),
        ),
        custom_builds(
            BaseXapiStatement,
            actor=custom_builds(BaseXapiIdentifiedGroupWithMboxSha1Sum),
        ),
        custom_builds(
            BaseXapiStatement,
            actor=custom_builds(BaseXapiIdentifiedGroupWithOpenId),
        ),
        custom_builds(
            BaseXapiStatement,
            actor=custom_builds(BaseXapiIdentifiedGroupWithAccount),
        ),
    ),
    st.data(),
)
def test_models_xapi_base_statement_with_invalid_group_objects(value, statement, data):
    """Test that the statement does not accept group agents with group members.

    An Anonymous Group MUST NOT contain Group Objects in the "member" identifiers.
    An Identified Group MUST NOT contain Group Objects in the "member" property.
    """
    kwargs = {"exclude_none": True}
    statement = statement.dict(**kwargs)
    statement["actor"]["member"] = [data.draw(custom_builds(value)).dict(**kwargs)]
    err = "actor -> member -> 0 -> objectType\n  unexpected value; permitted: 'Agent'"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize("path,value", [("actor__mbox", "mailto:example@mail.com")])
@custom_given(
    custom_builds(
        BaseXapiStatement,
        actor=custom_builds(BaseXapiIdentifiedGroupWithAccount),
    )
)
def test_models_xapi_base_statement_with_two_group_identifiers(path, value, statement):
    """Test that the statement does not accept multiple group identifiers.

    An Identified Group MUST include exactly one Inverse Functional Identifier.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="extra fields not permitted"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path,value",
    [
        ("object__id", "156e3f9f-4b56-4cba-ad52-1bd19e461d65"),
        ("object__stored", "2013-05-18T05:32:34.804+00:00"),
        ("object__version", "1.0.0"),
        ("object__authority", {"mbox": "mailto:example@mail.com"}),
    ],
)
@custom_given(
    custom_builds(BaseXapiStatement, object=custom_builds(BaseXapiSubStatement))
)
def test_models_xapi_base_statement_with_sub_statement_ref(path, value, statement):
    """Test that the sub-statement does not accept invalid properties.

    A SubStatement MUST NOT have the "id", "stored", "version" or "authority"
    properties.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="extra fields not permitted"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "value",
    [
        [{"id": "invalid whitespace"}],
        [{"id": "valid"}, {"id": "invalid whitespace"}],
        [{"id": "invalid_duplicate"}, {"id": "invalid_duplicate"}],
    ],
)
@custom_given(
    custom_builds(
        BaseXapiStatement,
        object=custom_builds(
            BaseXapiActivity,
            definition=custom_builds(BaseXapiActivityInteractionDefinition),
        ),
    )
)
def test_models_xapi_base_statement_with_invalid_interaction_object(value, statement):
    """Test that the statement does not accept invalid interaction fields.

    An interaction component's id value SHOULD NOT have whitespace.
    Within an array of interaction components, all id values MUST be distinct.
    """
    statement = statement.dict(exclude_none=True)
    path = "object.definition.scale".split(".")
    set_dict_value_from_path(statement, path, value)
    err = "(Duplicate InteractionComponents are not valid|string does not match regex)"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path,value",
    [
        ("context__revision", "Format is free"),
        ("context__platform", "FUN MOOC"),
    ],
)
@custom_given(
    st.one_of(
        custom_builds(BaseXapiStatement, object=custom_builds(BaseXapiSubStatement)),
        custom_builds(BaseXapiStatement, object=custom_builds(BaseXapiStatementRef)),
    ),
)
def test_models_xapi_base_statement_with_invalid_context_value(path, value, statement):
    """Test that the statement does not accept an invalid revision/platform value.

    The "revision" property MUST only be used if the Statement's Object is an Activity.
    The "platform" property MUST only be used if the Statement's Object is an Activity.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    err = "properties can only be used if the Statement's Object is an Activity"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize("path", ["context.contextActivities.not_parent"])
@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_with_invalid_context_activities(path, statement):
    """Test that the statement does not accept invalid context activity properties.

    Every key in the contextActivities Object MUST be one of parent, grouping, category,
    or other.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, path.split("."), {"id": "http://w3id.org/xapi"})
    with pytest.raises(ValidationError, match="extra fields not permitted"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "value",
    [
        {"id": "http://w3id.org/xapi"},
        [{"id": "http://w3id.org/xapi"}],
        [{"id": "http://w3id.org/xapi"}, {"id": "http://w3id.org/xapi/video"}],
    ],
)
@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_with_valid_context_activities(value, statement):
    """Test that the statement does accept valid context activities fields.

    Every value in the contextActivities Object MUST be either a single Activity Object
    or an array of Activity Objects.
    """
    statement = statement.dict(exclude_none=True)
    path = ["context", "contextActivities"]
    for activity in ["parent", "grouping", "category", "other"]:
        set_dict_value_from_path(statement, path + [activity], value)
    try:
        BaseXapiStatement(**statement)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")


@pytest.mark.parametrize("value", ["0.0.0", "1.1.0", "1", "2", "1.10.1", "1.0.1.1"])
@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_with_invalid_version(value, statement):
    """Test that the statement does not accept an invalid version field.

    An LRS MUST reject all Statements with a version specified that does not start with
    1.0.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, ["version"], value)
    with pytest.raises(ValidationError, match="version\n  string does not match regex"):
        BaseXapiStatement(**statement)


@custom_given(BaseXapiStatement)
def test_models_xapi_base_statement_with_valid_version(statement):
    """Test that the statement does accept a valid version field.

    Statements returned by an LRS MUST retain the version they are accepted with.
    If they lack a version, the version MUST be set to 1.0.0.
    """
    statement = statement.dict(exclude_none=True)
    set_dict_value_from_path(statement, ["version"], "1.0.3")
    assert "1.0.3" == BaseXapiStatement(**statement).model_dump()["version"]
    del statement["version"]
    assert "1.0.0" == BaseXapiStatement(**statement).model_dump()["version"]


@settings(deadline=None)
@pytest.mark.parametrize(
    "model",
    list(ModelSelector("ralph.models.xapi").model_rules),
)
@custom_given(st.data())
def test_models_xapi_base_statement_should_consider_valid_all_defined_xapi_models(
    model, data
):
    """Test that all defined xAPI models in the ModelSelector make valid statements."""
    # All specific xAPI models should inherit BaseXapiStatement
    assert issubclass(model, BaseXapiStatement)
    statement = data.draw(custom_builds(model)).json(exclude_none=True, by_alias=True)
    try:
        BaseXapiStatement(**json.loads(statement))
    except ValidationError as err:
        pytest.fail(f"Specific xAPI models should be valid BaseXapiStatements: {err}")
