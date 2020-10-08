"""
openassessmentblock.self_assess event schema definition
"""
from marshmallow import ValidationError, fields, validates_schema
from marshmallow.validate import Equal

from .base_ora_event import BaseOraEventSchema
from .peer_assess import PeerAssessEventSchema


class SelfAssessEventSchema(PeerAssessEventSchema):
    """Represents the event field of an
    openassessmentblock.self_assess event
    """

    score_type = fields.Str(
        required=True, validate=Equal(comparable="SE", error="score_type is not `SE`")
    )


class SelfAssessSchema(BaseOraEventSchema):
    """Represents the openassessmentblock.self_assess event
    This type of event is triggered after the user submits a
    self-assessment of his own response
    """

    event = fields.Nested(SelfAssessEventSchema(), required=True)
    event_type = fields.Str(
        required=True,
        validate=Equal(
            comparable="openassessmentblock.self_assess",
            error="The event event_type field is not `openassessmentblock.self_assess`",
        ),
    )

    # pylint: disable=no-self-use, unused-argument

    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """the event.context.path should end with:
        "self_assess"
        """
        valid_path = "/handler/self_assess"
        path = data["context"]["path"]
        path_len = len(valid_path)
        if path[-path_len:] != valid_path:
            raise ValidationError(
                f"context.path should end with: "
                f"{valid_path} "
                f"but {path[-path_len:]} does not match!"
            )
