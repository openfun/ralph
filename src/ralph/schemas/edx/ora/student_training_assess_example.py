"""
openassessment.student_training_assess_example event schema definition
"""
from marshmallow import Schema, ValidationError, fields, validates, validates_schema
from marshmallow.validate import Equal

from .base_ora_event import BaseOraEventSchema


class StudentTrainingAssessExampleEventSchema(Schema):
    """Represents the event field of an
    openassessment.student_training_assess_example
    """

    corrections = fields.Dict(keys=fields.Str(), values=fields.Str(), required=True)
    options_selected = fields.Dict(
        keys=fields.Str(), values=fields.Str(), required=True
    )
    submission_uuid = fields.UUID(required=True)

    # pylint: disable=no-self-use, unused-argument

    @validates("options_selected")
    def validate_options_selected(self, value):
        """"check options_selected is not a empty dictionnary"""
        if value:
            return
        raise ValidationError("options_selected can't be an empty dictionnary")

    @validates_schema
    def validate_corrections(self, data, **kwargs):
        """"check corrections field is empty or contains keys that are
        present in the options_selected dictionnary and that the values
        present in corrections and options_selected are different for
        the same key
        """
        if not data["corrections"]:
            return
        corrections_keys = set(data["corrections"].keys())
        options_selected_keys = set(data["options_selected"].keys())
        if not corrections_keys.issubset(options_selected_keys):
            raise ValidationError(
                "corrections may only contain keys present in options_selected"
            )
        for key in corrections_keys:
            if data["corrections"][key] != data["options_selected"]:
                continue
            raise ValidationError(
                f"corrections and options_selected value for key `{key}` should be different"
            )


class StudentTrainingAssessExampleSchema(BaseOraEventSchema):
    """Represents the openassessment.student_training_assess_example
    event. This type of event is triggered when a learner submits an assessment
    for an example response within a training step.
    """

    event = fields.Nested(StudentTrainingAssessExampleEventSchema(), required=True)
    event_type = fields.Str(
        required=True,
        validate=Equal(
            comparable="openassessment.student_training_assess_example",
            error=(
                "The event event_type field is not "
                "`openassessment.student_training_assess_example`"
            ),
        ),
    )

    # pylint: disable=no-self-use, unused-argument

    @validates_schema
    def validate_context_path(self, data, **kwargs):
        """the event.context.path should end with:
        "training_assess"
        """
        valid_path = "/handler/training_assess"
        path = data["context"]["path"]
        path_len = len(valid_path)
        if path[-path_len:] != valid_path:
            raise ValidationError(
                f"context.path should end with: "
                f"{valid_path} "
                f"but {path[-path_len:]} does not match!"
            )
