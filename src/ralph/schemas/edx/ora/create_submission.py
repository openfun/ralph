"""
openassessmentblock.create_submission event schema definition
"""
from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import UUID, DateTime, Dict, Int, List, Nested, Str
from marshmallow.validate import Equal

from .base_ora_event import BaseOraEventSchema

# pylint: disable=no-self-use, unused-argument


class CreateSubmissionEventAnswerSchema(Schema):
    """Represents the answer field of the event field
    of an openassessementblock.create_submission event
    """

    parts = List(Dict(values=Str()), required=True)
    file_keys = List(Str(), required=False)
    files_descriptions = List(Str(), required=False)

    @validates("parts")
    def validate_parts(self, value):
        """ "check if parts field contains dictionaries, their key-value
        pair is: `text`: `any string`
        """
        for obj in value:
            if set(obj.keys()) != {"text"}:
                raise ValidationError(
                    f"the dictionary {obj} should have only one key and it should be `text`"
                )


class CreateSubmissionEventSchema(Schema):
    """Represents the event field of an
    openassessmentblock.create_submission event
    """

    answer = Nested(CreateSubmissionEventAnswerSchema(), required=True)
    attempt_number = Int(required=True, strict=True)
    created_at = DateTime(format="iso", required=True)
    submission_uuid = UUID(required=True)
    submitted_at = DateTime(format="iso", required=True)


class CreateSubmissionSchema(BaseOraEventSchema):
    """Represents the openassessmentblock.create_submission event
    This type of event is triggered after the user submits a response
    for an open assessment block, peer assessment or a self assessment
    """

    event = Nested(CreateSubmissionEventSchema(), required=True)
    event_type = Str(
        required=True,
        validate=Equal(
            comparable="openassessmentblock.create_submission",
            error="The event event_type field is not `openassessmentblock.create_submission`",
        ),
    )

    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """the event.context.path should end with:
        "submit"
        """
        valid_path = "/handler/submit"
        path = data["context"]["path"]
        path_len = len(valid_path)
        if path[-path_len:] != valid_path:
            raise ValidationError(
                f"context.path should end with: "
                f"{valid_path} "
                f"but {path[-path_len:]} does not match!"
            )
