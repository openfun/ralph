"""
edx.problem.hint.feedback_displayed event schema definition
"""

from marshmallow import Schema, ValidationError, fields, validates_schema
from marshmallow.validate import Equal, Length, OneOf

from .base import BaseEventSchema, ContextSchema


class FeedbackDisplayedEventSchema(Schema):
    """Represents the event field of an
    edx.problem.hint.feedback_displayed
    """

    hint_label = fields.Str(required=True)
    problem_part_id = fields.Str(required=True)
    trigger_type = fields.Str(
        required=True,
        validate=OneOf(
            choices=["compound", "single"],
            error="The event trigger_type field value is not one of the valid values",
        ),
    )
    student_answer = fields.List(fields.Str(), required=True)
    choice_all = fields.List(fields.Str())
    correctness = fields.Boolean(required=True)
    question_type = fields.Str(
        required=True,
        validate=OneOf(
            choices=[
                "multiplechoiceresponse",
                "numericalresponse",
                "stringresponse",
                "optionresponse",
                "choiceresponse",
            ],
            error="The event question_type field value is not one of the valid values",
        ),
    )
    module_id = fields.Str(required=True)
    hints = fields.List(fields.Dict(keys=fields.Str()))

    # pylint: disable=no-self-use
    @validates_schema
    def validate_problem_part_id(self, data, **kwargs):
        """the event.problem_part_id should be contained in the
        event.module_id
        """
        if data["problem_part_id"][:32] != data["module_id"][-32:]:
            raise ValidationError(
                "event.problem_part_id should be contained in event.module_id"
            )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_trigger_type(self, data, **kwargs):
        """the event.trigger_type value should be "single" when the
        event.question_type is not "choiceresponse"
        """
        if (
            data["trigger_type"] != "single"
            and data["question_type"] != "choiceresponse"
        ):
            raise ValidationError(
                'event.trigger_type value should be "single" when the '
                'event.question_type is not "choiceresponse"'
            )

    # pylint: disable=no-self-use
    @validates_schema
    def validate_choice_all(self, data, **kwargs):
        """the event.choice_all should only be present when the
        event.question_type == "choiceresponse"
        """
        if "choice_all" in data and data["question_type"] != "choiceresponse":
            raise ValidationError(
                "event.choice_all should be only present "
                'when event.question_type == "choiceresponse"'
            )
        # the converse is true
        if "choice_all" not in data and data["question_type"] == "choiceresponse":
            raise ValidationError(
                'when event.question_type == "choiceresponse" - '
                "event.choice_all should be present"
            )


class FeedbackDisplayedSchema(BaseEventSchema):
    """Represents the edx.problem.hint.feedback_displayed event
    This type of event is triggered after the user submits an answer
    for a problem that include feedback messages
    """

    username = fields.Str(required=True, validate=Length(min=2, max=30))
    event_type = fields.Str(
        required=True,
        validate=Equal(
            comparable="edx.problem.hint.feedback_displayed",
            error='The event event_type field is not "edx.problem.hint.feedback_displayed"',
        ),
    )
    event = fields.Nested(FeedbackDisplayedEventSchema(), required=True)
    context = fields.Nested(ContextSchema(), required=True)
    page = fields.Str(
        required=True,
        validate=Equal(
            comparable="x_module", error='The event page field is not "x_module"'
        ),
    )
