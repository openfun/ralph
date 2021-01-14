"""
base event schema for ora (openassessment) events
"""
from marshmallow.fields import Nested, Str
from marshmallow.validate import Equal, Length

from ..base import BaseEventSchema, ContextSchema


class BaseOraEventSchema(BaseEventSchema):
    """Represents the Base Event Schema for events related to
    ora (openassessment) events
    """

    context = Nested(ContextSchema(), required=True)
    username = Str(required=True, validate=Length(min=2, max=30))
    page = Str(
        required=True,
        validate=Equal(
            comparable="x_module", error="The event page field is not `x_module`"
        ),
    )
