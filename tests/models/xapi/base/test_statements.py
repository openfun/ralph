"""Tests for the BaseXapiStatement."""

import json

import pytest
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

from tests.factories import ModelFactory, mock_xapi_instance


@pytest.mark.parametrize(
    "path",
    ["id", "stored", "verb__display", "result__score__raw"],
)
@pytest.mark.parametrize("value", [None, "", {}])
def test_models_xapi_base_statement_with_invalid_null_values(path, value):
    """Test that the statement does not accept any null values.

    XAPI-00001
    An LRS rejects with error code 400 Bad Request any Statement having a property whose
    value is set to "null", an empty object, or has no value, except in an "extensions"
    property.
    """
    statement = mock_xapi_instance(BaseXapiStatement)

    statement = statement.model_dump(exclude_none=True)
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
@pytest.mark.parametrize("value", [None, {}])
def test_models_xapi_base_statement_with_valid_null_values(path, value):
    """Test that the statement does accept valid null values in extensions fields.

    XAPI-00001
    An LRS rejects with error code 400 Bad Request any Statement having a property whose
    value is set to "null", an empty object, or has no value, except in an "extensions"
    property.
    """

    statement = mock_xapi_instance(
        BaseXapiStatement, object=mock_xapi_instance(BaseXapiActivity)
    )

    statement = statement.model_dump(exclude_none=True)

    set_dict_value_from_path(statement, path.split("__"), value)

    try:
        BaseXapiStatement(**statement)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")


@pytest.mark.parametrize("path", ["object__definition__correctResponsesPattern"])
def test_models_xapi_base_statement_with_valid_empty_array(path):
    """Test that the statement does accept a valid empty array.

    Where the Correct Responses Pattern contains an empty array, the meaning of this is
    that there is no correct answer.
    """

    statement = mock_xapi_instance(
        BaseXapiStatement,
        object=mock_xapi_instance(
            BaseXapiActivity,
            definition=mock_xapi_instance(BaseXapiActivityInteractionDefinition),
        ),
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), [])
    try:
        BaseXapiStatement(**statement)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")


@pytest.mark.parametrize(
    "field",
    ["actor", "verb", "object"],
)
def test_models_xapi_base_statement_must_use_actor_verb_and_object(field):
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

    statement = mock_xapi_instance(BaseXapiStatement)

    statement = statement.model_dump(exclude_none=True)
    del statement["context"]  # Necessary as context leads to another validation error
    del statement[field]
    with pytest.raises(ValidationError, match="Field required"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path,value,err",
    [
        ("actor__name", 1, "name\n  Input should be a valid string"),
        ("actor__account__name", 1, "account.name\n  Input should be a valid string"),
        (
            "actor__account__homePage",
            1,
            "homePage\n  Value error, '1' is not a valid 'IRI'",
        ),
        (
            "actor__account",
            ["foo", "bar"],
            (
                "account\n  Input should be a valid dictionary or instance of "
                "BaseXapiAccount"
            ),
        ),
        ("verb__display", ["foo"], "display\n  Input should be a valid dictionary"),
        ("verb__display", {"en": 1}, "display.en\n  Input should be a valid string"),
        ("object__id", ["foo"], "is not a valid 'IRI'"),
    ],
)
def test_models_xapi_base_statement_with_invalid_data_types(path, value, err):
    """Test that the statement does not accept values with wrong types.

    XAPI-00006
    An LRS rejects with error code 400 Bad Request a Statement which uses the wrong data
    type.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, actor=mock_xapi_instance(BaseXapiAgentWithAccount)
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)

    # err = "(type expected|not a valid dict|expected string )"

    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path,value,exception,err",
    [
        (
            "id",
            "0545fe73-1bbd-4f84-9c9a",
            ValidationError,
            "id\n  Input should be a valid UUID",
        ),
        (
            "actor",
            {"mbox": "example@mail.com"},
            TypeError,
            "Invalid `mailto:email` value",
        ),
        (
            "verb__display",
            {"bad language tag": "foo"},
            TypeError,
            "Invalid RFC 5646 Language tag",
        ),
        ("object__id", ["This is not an IRI"], ValidationError, "is not a valid 'IRI'"),
    ],
)
def test_models_xapi_base_statement_with_invalid_data_format(
    path, value, exception, err
):
    """Test that the statement does not accept values having a wrong format.

    XAPI-00007
    An LRS rejects with error code 400 Bad Request a Statement which uses any
    non-format-following key or value, including the empty string, where a string with a
    particular format (such as mailto IRI, UUID, or IRI) is required.
    (Empty strings are covered by XAPI-00001)
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, actor=mock_xapi_instance(BaseXapiAgentWithAccount)
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(exception, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize("path,value", [("actor__objecttype", "Agent")])
def test_models_xapi_base_statement_with_invalid_letter_cases(path, value):
    """Test that the statement does not accept keys having invalid letter cases.

    XAPI-00008
    An LRS rejects with error code 400 Bad Request a Statement where the case of a key
    does not match the case specified in this specification.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, actor=mock_xapi_instance(BaseXapiAgentWithAccount)
    )

    statement = statement.model_dump(exclude_none=True)
    if statement["actor"].get("objectType", None):
        del statement["actor"]["objectType"]
    set_dict_value_from_path(statement, path.split("__"), value)
    err = "(unexpected value|Extra inputs are not permitted)"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


def test_models_xapi_base_statement_should_not_accept_additional_properties():
    """Test that the statement does not accept additional properties.

    XAPI-00010
    An LRS rejects with error code 400 Bad Request a Statement where a key or value is
    not allowed by this specification.
    """
    statement = mock_xapi_instance(BaseXapiStatement)

    invalid_statement = statement.model_dump(exclude_none=True)
    invalid_statement["NEW_INVALID_FIELD"] = "some value"
    with pytest.raises(
        ValidationError, match="NEW_INVALID_FIELD\n  Extra inputs are not permitted"
    ):
        BaseXapiStatement(**invalid_statement)


@pytest.mark.parametrize("path,value", [("object__id", "w3id.org/xapi/video")])
def test_models_xapi_base_statement_with_iri_without_scheme(path, value):
    """Test that the statement does not accept IRIs without a scheme.

    XAPI-00011
    An LRS rejects with error code 400 Bad Request a Statement containing IRL or IRI
    values without a scheme.
    """
    statement = mock_xapi_instance(BaseXapiStatement)

    statement = statement.model_dump(exclude_none=True)
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
def test_models_xapi_base_statement_with_invalid_extensions(path):
    """Test that the statement does not accept extensions keys with invalid IRIs.

    XAPI-00118
    An Extension "key" is an IRI. The LRS rejects with 400 a statement which has an
    extension key which is not a valid IRI, if an extension object is present.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, object=mock_xapi_instance(BaseXapiActivity)
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), "")
    with pytest.raises(ValidationError, match="is not a valid 'IRI'"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize("path,value", [("actor__mbox", "mailto:example@mail.com")])
def test_models_xapi_base_statement_with_two_agent_types(path, value):
    """Test that the statement does not accept multiple agent types.

    An Agent MUST NOT include more than one Inverse Functional Identifier.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, actor=mock_xapi_instance(BaseXapiAgentWithAccount)
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BaseXapiStatement(**statement)


def test_models_xapi_base_statement_missing_member_property():
    """Test that the statement does not accept group agents with missing members.

    An Anonymous Group MUST include a "member" property listing constituent Agents.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, actor=mock_xapi_instance(BaseXapiAnonymousGroup)
    )

    statement = statement.model_dump(exclude_none=True)
    del statement["actor"]["member"]
    with pytest.raises(ValidationError, match="member\n  Field required"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "klass",
    [
        BaseXapiAnonymousGroup,
        BaseXapiIdentifiedGroupWithMbox,
        BaseXapiIdentifiedGroupWithMboxSha1Sum,
        BaseXapiIdentifiedGroupWithOpenId,
        BaseXapiIdentifiedGroupWithAccount,
    ],
)
def test_models_xapi_base_statement_with_invalid_group_objects(klass):
    """Test that the statement does not accept group agents with group members.

    An Anonymous Group MUST NOT contain Group Objects in the "member" identifiers.
    An Identified Group MUST NOT contain Group Objects in the "member" property.
    """

    actor_class = ModelFactory.__random__.choice(
        [
            BaseXapiAnonymousGroup,
            BaseXapiIdentifiedGroupWithMbox,
            BaseXapiIdentifiedGroupWithMboxSha1Sum,
            BaseXapiIdentifiedGroupWithOpenId,
            BaseXapiIdentifiedGroupWithAccount,
        ]
    )
    statement = mock_xapi_instance(
        BaseXapiStatement, actor=mock_xapi_instance(actor_class)
    )

    kwargs = {"exclude_none": True}
    statement = statement.model_dump(**kwargs)
    statement["actor"]["member"] = [mock_xapi_instance(klass).model_dump(**kwargs)]

    for class_ in [
        "BaseXapiAgentWithMbox",
        "BaseXapiAgentWithMboxSha1Sum",
        "BaseXapiAgentWithOpenId",
        "BaseXapiAgentWithAccount",
    ]:
        err = (
            f"actor.BaseXapiAnonymousGroup.member.0.{class_}.objectType\n  "
            "Input should be 'Agent'"
        )
        with pytest.raises(ValidationError, match=err):
            BaseXapiStatement(**statement)


@pytest.mark.parametrize("path,value", [("actor__mbox", "mailto:example@mail.com")])
def test_models_xapi_base_statement_with_two_group_identifiers(path, value):
    """Test that the statement does not accept multiple group identifiers.

    An Identified Group MUST include exactly one Inverse Functional Identifier.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, actor=mock_xapi_instance(BaseXapiIdentifiedGroupWithAccount)
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
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
def test_models_xapi_base_statement_with_sub_statement_ref(path, value):
    """Test that the sub-statement does not accept invalid properties.

    A SubStatement MUST NOT have the "id", "stored", "version" or "authority"
    properties.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement, object=mock_xapi_instance(BaseXapiSubStatement)
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "value,err",
    [
        ([{"id": "invalid whitespace"}], "String should match pattern"),
        (
            [{"id": "valid"}, {"id": "invalid whitespace"}],
            "String should match pattern",
        ),
        (
            [{"id": "invalid_duplicate"}, {"id": "invalid_duplicate"}],
            "Duplicate InteractionComponents are not valid",
        ),
    ],
)
def test_models_xapi_base_statement_with_invalid_interaction_object(value, err):
    """Test that the statement does not accept invalid interaction fields.

    An interaction component's id value SHOULD NOT have whitespace.
    Within an array of interaction components, all id values MUST be distinct.
    """
    statement = mock_xapi_instance(
        BaseXapiStatement,
        object=mock_xapi_instance(
            BaseXapiActivity,
            definition=mock_xapi_instance(BaseXapiActivityInteractionDefinition),
        ),
    )

    statement = statement.model_dump(exclude_none=True)
    path = "object.definition.scale".split(".")
    set_dict_value_from_path(statement, path, value)
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "path,value",
    [
        ("context__revision", "Format is free"),
        ("context__platform", "FUN MOOC"),
    ],
)
def test_models_xapi_base_statement_with_invalid_context_value(path, value):
    """Test that the statement does not accept an invalid revision/platform value.

    The "revision" property MUST only be used if the Statement's Object is an Activity.
    The "platform" property MUST only be used if the Statement's Object is an Activity.
    """

    object_class = ModelFactory.__random__.choice(
        [
            BaseXapiSubStatement,
            BaseXapiStatementRef,
        ]
    )
    statement = mock_xapi_instance(
        BaseXapiStatement, object=mock_xapi_instance(object_class)
    )

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("__"), value)
    err = "properties can only be used if the Statement's Object is an Activity"
    with pytest.raises(ValidationError, match=err):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize("path", ["context.contextActivities.not_parent"])
def test_models_xapi_base_statement_with_invalid_context_activities(path):
    """Test that the statement does not accept invalid context activity properties.

    Every key in the contextActivities Object MUST be one of parent, grouping, category,
    or other.
    """
    statement = mock_xapi_instance(BaseXapiStatement)

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, path.split("."), {"id": "http://w3id.org/xapi"})
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BaseXapiStatement(**statement)


@pytest.mark.parametrize(
    "value",
    [
        {"id": "http://w3id.org/xapi"},
        [{"id": "http://w3id.org/xapi"}],
        [{"id": "http://w3id.org/xapi"}, {"id": "http://w3id.org/xapi/video"}],
    ],
)
def test_models_xapi_base_statement_with_valid_context_activities(value):
    """Test that the statement does accept valid context activities fields.

    Every value in the contextActivities Object MUST be either a single Activity Object
    or an array of Activity Objects.
    """
    statement = mock_xapi_instance(BaseXapiStatement)

    statement = statement.model_dump(exclude_none=True)
    path = ["context", "contextActivities"]
    for activity in ["parent", "grouping", "category", "other"]:
        set_dict_value_from_path(statement, path + [activity], value)
    try:
        BaseXapiStatement(**statement)
    except ValidationError as err:
        pytest.fail(f"Valid statement should not raise exceptions: {err}")


@pytest.mark.parametrize("value", ["0.0.0", "1.1.0", "1", "2", "1.10.1", "1.0.1.1"])
def test_models_xapi_base_statement_with_invalid_version(value):
    """Test that the statement does not accept an invalid version field.

    An LRS MUST reject all Statements with a version specified that does not start with
    1.0.
    """
    statement = mock_xapi_instance(BaseXapiStatement)

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, ["version"], value)
    with pytest.raises(ValidationError, match="version\n  String should match pattern"):
        BaseXapiStatement(**statement)


def test_models_xapi_base_statement_with_valid_version():
    """Test that the statement does accept a valid version field.

    Statements returned by an LRS MUST retain the version they are accepted with.
    If they lack a version, the version MUST be set to 1.0.0.
    """
    statement = mock_xapi_instance(BaseXapiStatement)

    statement = statement.model_dump(exclude_none=True)
    set_dict_value_from_path(statement, ["version"], "1.0.3")
    assert "1.0.3" == BaseXapiStatement(**statement).model_dump()["version"]
    del statement["version"]
    assert "1.0.0" == BaseXapiStatement(**statement).model_dump()["version"]


@pytest.mark.parametrize(
    "model",
    list(ModelSelector("ralph.models.xapi").model_rules),
)
def test_models_xapi_base_statement_should_consider_valid_all_defined_xapi_models(
    model,
):
    """Test that all defined xAPI models in the ModelSelector make valid statements."""

    # All specific xAPI models should inherit BaseXapiStatement
    assert issubclass(model, BaseXapiStatement)
    statement = mock_xapi_instance(model)
    statement = statement.json(exclude_none=True, by_alias=True)
    try:
        BaseXapiStatement(**json.loads(statement))
    except ValidationError as err:
        pytest.fail(f"Specific xAPI models should be valid BaseXapiStatements: {err}")
