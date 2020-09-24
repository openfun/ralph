"""
edx.problem.hint.feedback_displayed event schema definition
"""

from marshmallow import Schema, ValidationError, fields, validates_schema
from marshmallow.validate import Equal, Length, OneOf

from .base import BaseEventSchema, ContextSchema
from .browser import MD5_HASH_LEN


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
                "choiceresponse",
                "multiplechoiceresponse",
                "numericalresponse",
                "optionresponse",
                "stringresponse",
            ],
            error="Not allowed value",
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
        if data["problem_part_id"][:MD5_HASH_LEN] != data["module_id"][-MD5_HASH_LEN:]:
            raise ValidationError("problem_part_id should be in module_id")

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
                "choice_all should be only present when the question_type is `choiceresponse`"
            )

        if data["question_type"] == "choiceresponse" and "choice_all" not in data:
            raise ValidationError(
                "When the question_type is `choiceresponse`, choice_all should be present"
            )


class FeedbackDisplayedSchema(BaseEventSchema):
    """Represents the edx.problem.hint.feedback_displayed event
    This type of event is triggered after the user submits an answer
    for a problem that include feedback messages
    """

    # pylint: disable=no-self-use
    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """the event.context.path should end with:
        "xmodule_hanlder/problem_check"
        """
        valid_path = "xmodule_handler/problem_check"
        path = data["context"]["path"]
        path_len = len(valid_path)
        if path[-path_len:] != valid_path:
            raise ValidationError(
                f"context.path should end with: "
                f"{valid_path} "
                f"but {path[-path_len:]} does not match!"
            )

    username = fields.Str(required=True, validate=Length(min=2, max=30))
    event_type = fields.Str(
        required=True,
        validate=Equal(
            comparable="edx.problem.hint.feedback_displayed",
            error="The event event_type field is not `edx.problem.hint.feedback_displayed`",
        ),
    )
    event = fields.Nested(FeedbackDisplayedEventSchema(), required=True)
    context = fields.Nested(ContextSchema(), required=True)
    page = fields.Str(
        required=True,
        validate=Equal(
            comparable="x_module", error="The event page field is not `x_module`"
        ),
    )
