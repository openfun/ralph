"""
openassessmentblock.peer_assess event schema definition
"""
from marshmallow import Schema, ValidationError, fields, validates_schema
from marshmallow.validate import Equal, Length

from .base_ora_event import BaseOraEventSchema


class PeerAssessEventPartsOptionSchema(Schema):
    """Represents the event.parts.option field"""

    name = fields.Str(required=True)
    points = fields.Integer(required=True, strict=True)


class PeerAssessEventPartsCriterionSchema(Schema):
    """Represents the event.parts.criterion field"""

    name = fields.Str(required=True)
    points_possible = fields.Integer(required=True, strict=True)


class PeerAssessEventPartsSchema(Schema):
    """Represents the event.parts field"""

    option = fields.Nested(
        PeerAssessEventPartsOptionSchema(), required=True, allow_none=True
    )
    criterion = fields.Nested(PeerAssessEventPartsCriterionSchema(), required=True)
    feedback = fields.Str(required=True)


class PeerAssessEventRubricSchema(Schema):
    """Represents the event.rubric field"""

    content_hash = fields.Str(required=True, validate=Length(min=40, max=40))


class PeerAssessEventSchema(Schema):
    """Represents the event field of an
    openassessmentblock.peer_assess event
    """

    feedback = fields.Str(required=True)
    parts = fields.List(fields.Nested(PeerAssessEventPartsSchema()), required=True)
    rubric = fields.Nested(PeerAssessEventRubricSchema)
    scored_at = fields.DateTime(format="iso", required=True)
    scorer_id = fields.Str(required=True, validate=Length(min=32, max=32))
    score_type = fields.Str(
        required=True, validate=Equal(comparable="PE", error="score_type is not `PE`")
    )
    submission_uuid = fields.UUID(required=True)


class PeerAssessSchema(BaseOraEventSchema):
    """Represents the openassessmentblock.peer_assess event
    This type of event is triggered after the user submits an
    assessment of a peer’s response
    """

    event = fields.Nested(PeerAssessEventSchema(), required=True)
    event_type = fields.Str(
        required=True,
        validate=Equal(
            comparable="openassessmentblock.peer_assess",
            error="The event event_type field is not `openassessmentblock.peer_assess`",
        ),
    )

    # pylint: disable=no-self-use, unused-argument

    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """the event.context.path should end with:
        "peer_assess"
        """
        valid_path = "/handler/peer_assess"
        path = data["context"]["path"]
        path_len = len(valid_path)
        if path[-path_len:] != valid_path:
            raise ValidationError(
                f"context.path should end with: "
                f"{valid_path} "
                f"but {path[-path_len:]} does not match!"
            )
