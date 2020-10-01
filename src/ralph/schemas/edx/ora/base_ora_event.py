"""
base event schema for ora (openassessment) events
"""
from marshmallow import fields
from marshmallow.validate import Equal, Length

from ..base import BaseEventSchema, ContextSchema


class BaseOraEventSchema(BaseEventSchema):
    """Represents the Base Event Schema for events related to
    ora (openassessment) events
    """

    context = fields.Nested(ContextSchema(), required=True)
    username = fields.Str(required=True, validate=Length(min=2, max=30))
    page = fields.Str(
        required=True,
        validate=Equal(
            comparable="x_module", error="The event page field is not `x_module`"
        ),
    )
