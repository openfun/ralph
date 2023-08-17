"""xAPI JSON-LD Profile."""

from datetime import datetime
from typing import Optional, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from jsonpath_ng.exceptions import JsonPathParserError
from jsonpath_ng.parser import JsonPathParser
from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for
from pydantic import AnyUrl, BaseModel, Field, Json, conlist, constr, root_validator

from ralph.models.selector import selector
from ralph.models.xapi.base.common import IRI, LanguageMap
from ralph.models.xapi.base.unnested_objects import (
    BaseXapiActivityDefinition,
    BaseXapiActivityInteractionDefinition,
)

# NB: These pydantic models should follow the profile structure specification.
# See: https://github.com/adlnet/xapi-profiles/blob/master/xapi-profiles-structure.md


class JsonPath(str):
    """Pydantic custom data type validating JSONPaths."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(path: str):
            """Check whether the provided `path` is a valid JSONPath."""
            if not path:
                raise ValueError("Invalid JSONPath: empty string is not a valid path")
            try:
                JsonPathParser().parse(path)
            except JsonPathParserError as error:
                raise ValueError(f"Invalid JSONPath: {error}") from error
            return cls(path)

        yield validate


class JSONSchema(dict):
    """Pydantic custom data type validating JSONSchemas."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(schema: dict):
            """Check whether the provided `schema` is a valid JSONSchema."""
            try:
                validator_for(schema).check_schema(schema)
            except SchemaError as error:
                raise ValueError(f"Invalid JSONSchema: {error}") from error
            return cls(schema)

        yield validate


class ProfilePattern(BaseModel):
    """Profile `pattern` field.

    Attributes:
        id (URI): A URI for the Pattern.
        type (str): Equal to `Pattern`.
        primary (bool): Only primary Patterns are checked for matching sequences of
            Statements.
        inScheme (IRI): The IRI of the specific Profile version.
        prefLabel (dict): A Language Map of descriptive names for the Pattern.
        definition (dict): A Language Map of descriptions of the purpose and usage of
            the Pattern.
        deprecated (bool): If true, this Pattern is deprecated.
        alternates (list): A list of Pattern or Statement Template identifiers.
            An alternates Pattern matches if any member of the list matches.
        optional (URI): A single Pattern or Statement Template identifier.
            An `optional` Pattern matches if the identified thing matches once, or is
            not present at all.
        oneOrMore (URI): A single Pattern or Statement Template identifier.
            A `oneOrMore` Pattern matches if the identified thing matches once, or any
            number of times more than once.
        sequence (list): A list of Pattern or Statement Template identifiers.
            A sequence Pattern matches if the identified things match in the order
            specified.
        zeroOrMore (URI): A single Pattern or Statement Template identifier.
            A `zeroOrMore` Pattern matches if the identified thing is not present or is
            present one or more times.
    """

    id: AnyUrl
    type: Literal["Pattern"]
    primary: Optional[bool] = False
    inScheme: Optional[IRI]
    prefLabel: Optional[LanguageMap]
    definition: Optional[LanguageMap]
    deprecated: Optional[bool] = False
    alternates: Optional[conlist(AnyUrl, min_items=1)]
    optional: Optional[AnyUrl]
    oneOrMore: Optional[AnyUrl]
    sequence: Optional[conlist(AnyUrl, min_items=1)]
    zeroOrMore: Optional[AnyUrl]

    @root_validator()
    @classmethod
    def check_pattern_requirements(cls, values):
        """Check `primary` pattern requirements and matching rules."""
        primary = values.get("primary")
        pref_label = values.get("prefLabel")
        definition = values.get("definition")
        if primary and not (pref_label and definition):
            raise ValueError(
                "A `primary` pattern MUST include `prefLabel` and `definition` fields"
            )
        rules = ["alternates", "optional", "oneOrMore", "sequence", "zeroOrMore"]
        if sum(1 for rule in rules if values.get(rule)) != 1:
            raise ValueError(
                "A pattern MUST contain exactly one of `alternates`, `optional`, "
                "`oneOrMore`, `sequence`, and `zeroOrMore` fields"
            )
        return values


class ProfileTemplateRule(BaseModel):
    """Profile `templates.rules` field.

    Note:
        We do not validate the following requirements:
        - A Statement Template Rule MUST include one or more of
          `presence`, `any`, `all` or `none`.
          > We accept statement rules not including any of
            `presence`, `any`, `all` or `none`.

    Attributes:
        location (str): A JSONPath string. This is evaluated on a Statement to find the
            evaluated values to apply the requirements in this rule to.
            All evaluated values from location are matchable values.
        selector (str):  JSONPath string. If specified, this JSONPath is evaluated on
            each member of the evaluated values resulting from the location selector,
            and the resulting values become the evaluated values instead.
            If it returns nothing on a location, that represents an unmatchable value
            for that location, meaning all will fail, as will a presence of included.
            All other values returned are matchable values.
        presence (str): Equal to `included`, `excluded` or `recommended`.
        any (list): A list of values that needs to intersect with the matchable values.
        all (list): A list of values which all the evaluated values need to be from.
        none (list): A list of values that can't be in the matchable values.
        scopeNote (dict): A Language Map describing usage details for the parts of
            Statements addressed by this rule.
            For example, a Profile with a rule requiring `result.duration` might provide
            guidance on how to calculate it.
    """

    location: JsonPath
    selector: Optional[JsonPath]
    presence: Optional[Literal["included", "excluded", "recommended"]]
    any: Optional[conlist(Union[str, int, bool, list, dict, None], min_items=1)]
    all: Optional[conlist(Union[str, int, bool, list, dict, None], min_items=1)]
    none: Optional[conlist(Union[str, int, bool, list, dict, None], min_items=1)]
    scopeNote: Optional[LanguageMap]


class ProfileTemplate(BaseModel):
    """Profile `templates` field.

    Note:
        We do not validate the following requirements:
        - A Statement Template MUST NOT have both `objectStatementRefTemplate` and
          `objectActivityType`.
          > We accept both `objectStatementRefTemplate` and `objectActivityType`.

    Attributes:
        id (URI): A URI for this Statement Template.
        type (str): Equal to `StatementTemplate`.
        inScheme (IRI): The IRI of the specific Profile version.
        prefLabel (dict): A Language Map of descriptive names for the Statement
            Template.
        definition (dict): A Language Map of descriptions of the purpose and usage of
            the Statement Template.
        deprecated (bool): If true, this Statement Template is deprecated.
        verb (IRI): The verb IRI.
        objectActivityType (IRI): The object activity type IRI.
        contextGroupingActivityType (list): A List of contextActivities grouping
            activity type IRIs.
        contextParentActivityType (list): A list of contextActivities parent activity
            type IRIs.
        contextOtherActivityType (list): A list of contextActivities other activity type
            IRIs.
        contextCategoryActivityType (list): A list of contextActivities category
            activity type IRIs.
        attachmentUsageType (list): A list of attachment usage type IRIs.
        objectStatementRefTemplate (list): A list of Statement Template identifiers.
        contextStatementRefTemplate (list): A list of Statement Template identifiers.
        rules (list): Array of Statement Template Rules. See `ProfileTemplateRule`.
    """

    id: AnyUrl
    type: Literal["StatementTemplate"]
    inScheme: IRI
    prefLabel: LanguageMap
    definition: LanguageMap
    deprecated: Optional[bool] = False
    verb: Optional[IRI]
    objectActivityType: Optional[IRI]
    contextGroupingActivityType: Optional[conlist(IRI, min_items=1)]
    contextParentActivityType: Optional[conlist(IRI, min_items=1)]
    contextOtherActivityType: Optional[conlist(IRI, min_items=1)]
    contextCategoryActivityType: Optional[conlist(IRI, min_items=1)]
    attachmentUsageType: Optional[conlist(IRI, min_items=1)]
    objectStatementRefTemplate: Optional[conlist(AnyUrl, min_items=1)]
    contextStatementRefTemplate: Optional[conlist(AnyUrl, min_items=1)]
    rules: Optional[conlist(ProfileTemplateRule, min_items=1)]


class ProfileVerbActivityAttachmentConcept(BaseModel):
    """Profile `concepts` field for a Verb, Activity Type, and Attachment Usage Type.

    Attributes:
        id (IRI): The IRI of this Concept.
        type (str): Equal to `Verb`, `ActivityType`, or `AttachmentUsageType`.
        inScheme (IRI): The IRI of the Profile version.
        prefLabel (dict): A Language Map of the preferred names in each language.
        definition (dict): A Language Map of the definition how to use the Concept.
        deprecated (bool): If true, this Concept is deprecated.
        broader (list): A list of IRIs of Concepts of the same type from this Profile
            version that have a broader meaning.
        broadMatch (list): A list of IRIs of Concepts of the same type from a different
            Profile that have a broader meaning.
        narrower (list): A list of IRIs of Concepts of the same type from this Profile
            version that have a narrower meaning.
        narrowMatch (list): A list of IRIs of Concepts of the same type from different
            Profiles that have narrower meanings.
        related (list): A list of IRIs of Concepts of the same type from this Profile
            version that are close to this Concept's meaning.
        relatedMatch (list): A list of IRIs of Concepts of the same type from a
            different Profile or a different version of the same Profile that has a
            related meaning that is not clearly narrower or broader.
        exactMatch (list): A list of IRIs of Concepts of the same type from a different
            Profile or a different version of the same Profile that have exactly the
            same meaning.
    """

    id: IRI
    type: Literal["Verb", "ActivityType", "AttachmentUsageType"]
    inScheme: IRI
    prefLabel: LanguageMap
    definition: LanguageMap
    deprecated: Optional[bool] = False
    broader: Optional[conlist(IRI, min_items=1)]
    broadMatch: Optional[conlist(IRI, min_items=1)]
    narrower: Optional[conlist(IRI, min_items=1)]
    narrowMatch: Optional[conlist(IRI, min_items=1)]
    related: Optional[conlist(IRI, min_items=1)]
    relatedMatch: Optional[conlist(IRI, min_items=1)]
    exactMatch: Optional[conlist(IRI, min_items=1)]


class ProfileExtensionConcept(BaseModel):
    """Profile `concepts` field for an Extension.

    Note:
        We do not validate the following requirements:
        - `recommendedActivityTypes` is only allowed if `type` is `ActivityExtension`.
          > We accept `recommendedActivityTypes` with other types too.
        - `recommendedVerbs` is only allowed if `type` is not `ActivityExtension`.
          > We accept `recommendedVerbs` if `type` is `ActivityExtension`.
        - Profiles MUST use at most one of `schema` and `inlineSchema`.
          > We accept having both `schema` and `inlineSchema` set.
        - In the spec the type of `inlineSchema` is object, however in the description
          it is stated that it's a string value.
          > We accept both - string and dict values in the `inlineSchema` field.

    Attributes:
        id (IRI): The IRI of the extension, used as the extension key in xAPI.
        type (): Equal to `ContextExtension`, `ResultExtension`, or `ActivityExtension`.
        inScheme (IRI): The IRI of the Profile version.
        prefLabel (dict): A Language Map of descriptive names for the extension.
        definition (dict): A Language Map of descriptions of the purpose and usage of
            the extension.
        deprecated (bool): If true, this Concept is deprecated.
        recommendedActivityTypes (list): A list of activity type URIs that this
            extension is recommended for use with (extending to narrower of the same).
        recommendedVerbs (list): A list of verb URIs that this extension is recommended
            for use with (extending to narrower of the same).
        context (IRI): The IRI of a JSON-LD context for this extension.
        schema (IRI): The IRI for accessing a JSON Schema for this extension.
        inlineSchema (str or dict): An alternate way to include a JSON Schema.
    """

    id: IRI
    type: Literal["ContextExtension", "ResultExtension", "ActivityExtension"]
    inScheme: IRI
    prefLabel: LanguageMap
    definition: LanguageMap
    deprecated: Optional[bool] = False
    recommendedActivityTypes: Optional[conlist(AnyUrl, min_items=1)]
    recommendedVerbs: Optional[conlist(AnyUrl, min_items=1)]
    context: Optional[IRI]
    schemaIRI: Optional[IRI] = Field(alias="schema")  # schema name reserved in pydantic
    inlineSchema: Optional[
        Union[Json[JSONSchema], JSONSchema]  # pylint: disable=unsubscriptable-object
    ]


class ProfileDocumentResourceConcept(BaseModel):
    """Profile `concepts` field for a Document Resource.

    Note:
        We do not validate the following requirements:
        - `contentType` should be a media type following RFC 2046.
          > We accept any string for the `contentType` field.
        - Profiles MUST use at most one of `schema` and `inlineSchema`.
          > We accept having both `schema` and `inlineSchema` set.
        - In the spec the type of `inlineSchema` is object, however in the description
          it is stated that it's a string value.
          > We accept both - string and dict values in the `inlineSchema` field.

    Attributes:
        id (IRI): The IRI of the document resource, used as the stateId/profileId in
            xAPI.
        type (str): Equal to `StateResource`, `AgentProfileResource` or
            `ActivityProfileResource`.
        inScheme (IRI): The IRI of the specific Profile version.
        prefLabel (dict): A Language Map of descriptive names for the document resource.
        definition (dict): A Language Map of descriptions of the purpose and usage of
            the document resource.
        contentType (str): The media type for the resource, as described in RFC 2046
            (e.g. application/json).
        deprecated (bool): If true, this Concept is deprecated.
        context (IRI): The IRI of a JSON-LD context for this document resource.
        schema (IRI): The IRI for accessing a JSON Schema for this document resource.
        inlineSchema (str or dict): An alternate way to include a JSON Schema.
    """

    id: IRI
    type: Literal["StateResource", "AgentProfileResource", "ActivityProfileResource"]
    inScheme: IRI
    prefLabel: LanguageMap
    definition: LanguageMap
    contentType: constr(min_length=1)  # media type for the resource as in RFC 2046
    deprecated: Optional[bool] = False
    context: Optional[IRI]
    schemaIRI: Optional[IRI] = Field(alias="schema")  # schema name reserved in pydantic
    inlineSchema: Optional[
        Union[Json[JSONSchema], JSONSchema]  # pylint: disable=unsubscriptable-object
    ]


class ProfileActivityDefinition(BaseXapiActivityDefinition):
    """Profile `concepts.activityDefinition` field."""

    context: Literal["https://w3id.org/xapi/profiles/activity-context"] = Field(
        alias="@context"
    )


class ProfileActivityInteractionDefinition(BaseXapiActivityInteractionDefinition):
    """Profile `concepts.activityDefinition` field."""

    context: Literal["https://w3id.org/xapi/profiles/activity-context"] = Field(
        alias="@context"
    )


class ProfileActivityConcept(BaseModel):
    """Profile `concepts` field for an Activity.

    Attributes:
        id (IRI): The IRI of the activity.
        type (str): Equal to `Activity`.
        inScheme (IRI): The IRI of the specific Profile version.
        deprecated (bool): If true, this Concept is deprecated.
        activityDefinition (dict): An Activity Definition as in xAPI including a
            `@context` field.
    """

    id: IRI
    type: Literal["Activity"]
    inScheme: IRI
    deprecated: Optional[bool] = False
    activityDefinition: Union[
        ProfileActivityDefinition, ProfileActivityInteractionDefinition
    ]


ProfileConcept = Union[
    ProfileVerbActivityAttachmentConcept,
    ProfileExtensionConcept,
    ProfileDocumentResourceConcept,
    ProfileActivityConcept,
]


class ProfileAuthor(BaseModel):
    """Profile `author` field.

    Attributes:
        type (str): Equal to `Organization` or `Person`.
        name (str): A string with the name of the organization or person.
        url (URL): A URL for the Person or Group.
    """

    type: Literal["Organization", "Person"]
    name: constr(min_length=1)
    url: Optional[AnyUrl]


class ProfileVersion(BaseModel):
    """Profile `version` field.

    Attributes:
        id (IRI): The IRI of the version ID.
        wasRevisionOf (list): A list of IRIs of all Profile versions this version was
            written as a revision of.
        generatedAtTime (datetime): The date this version was created on.
    """

    id: IRI
    wasRevisionOf: Optional[conlist(IRI, min_items=1)]
    generatedAtTime: datetime


class Profile(BaseModel):
    """xAPI JSON-LD profile.

    Note:
        We do not validate the following requirements:
        - All properties that are not JSON-LD keywords (or aliases thereof) MUST expand
          to absolute IRIs during processing as defined in the JSON-LD specification.
          > We don't validate/process JSON-LD keyword expansion.
        - All properties that are not JSON-LD keywords (or aliases thereof) and not
          described by this specification MUST be expressed using compact IRIs or
          absolute IRIs.
          > We ignore all properties that are not defined in the `Profile` model.
        - The `@context` could be array-valued.
          > We only support `@context` with a string value.

    Attributes:
        id (IRI): The IRI of the Profile overall (not a specific version).
        @context (URI): Equal to `https://w3id.org/xapi/profiles/context`.
        type (str): Equal to `Profile`.
        conformsTo (URI): URI of the Profile specification version conformed to.
        prefLabel (dict): Language map of names for this Profile.
        definition (dict): Language map of descriptions for this Profile.
        seeAlso (URL): A URL containing information about the Profile.
        versions (list): A list of `ProfileVersion` objects for this Profile.
        author (dict): An Organization or Person. See `ProfileAuthor`.
        concepts (list): A list of Concepts that make up this Profile.
        templates (list): A list of Statement Templates for this Profile.
        patterns (list): A list of Patterns for this Profile.
    """

    __selector__ = selector(type="Profile")

    id: IRI
    context: Literal["https://w3id.org/xapi/profiles/context"] = Field(alias="@context")
    type: Literal["Profile"]
    conformsTo: AnyUrl
    prefLabel: LanguageMap
    definition: LanguageMap
    seeAlso: Optional[AnyUrl]
    versions: conlist(ProfileVersion, min_items=1)
    author: ProfileAuthor
    concepts: Optional[conlist(ProfileConcept, min_items=1)]
    templates: Optional[conlist(ProfileTemplate, min_items=1)]
    patterns: Optional[conlist(ProfilePattern, min_items=1)]
